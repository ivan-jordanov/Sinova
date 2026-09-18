"""
Preprocessing pipeline — CPU-bound frame/slice work runs in a PERSISTENT
ProcessPoolExecutor (created once, on first use, and reused for every
subsequent job) instead of a per-job pool.

Why persistent: with spawn (Windows' only option, and a good idea on
every platform for NumPy-heavy code), each worker process re-imports
NumPy/SciPy/TomoPy. Paying that ~2-4s / 1.5-3GB cost on every job is
what a per-job "with ProcessPoolExecutor() as pool:" does. Creating the
pool once and reusing its already-warm workers for the app's lifetime
pays that cost exactly once. Only the FIRST job after the app starts (or
the app's own startup hook, if you pre-warm it — see the bottom of this
file) eats the spawn latency.

Why the worker functions look the way they do (pickling): a persistent
pool means workers are long-lived, separate interpreters — they never
share memory with the parent, and (especially on spawn) can only receive
what can be pickled. We never send `job_manager`, `dataset_service`, or
`workspace` into a worker: those are exactly the kind of stateful,
per-process objects (locks, file handles, DB/socket connections) that
either fail to pickle or silently misbehave if half-reconstructed in a
child. Instead, workers receive only:
  - a small, explicitly-picklable `_MemmapDescriptor` (file path + shape
    + dtype) that lets a worker open its OWN np.memmap onto the same
    underlying file — writes to non-overlapping index ranges from
    different processes are visible across processes because memmap
    uses a shared (MAP_SHARED) OS page cache for the file, not because
    anything is being copied between processes;
  - the chunk's index range;
  - the (assumed-simple/picklable) operations config.
job_manager stays in the parent; only the parent updates progress or
checks cancellation, using each chunk's returned item-count.
"""

import asyncio
import atexit
import concurrent.futures
import multiprocessing
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from app.schemas.preprocessing import Operation, PreprocessingConfiguration
from app.services.business.dataset_access import DatasetService, get_dataset_service
from app.services.business.export_service import ExportService
from app.services.business.job_manager import JobManager, get_job_manager
from app.services.business.operation_executor import apply_operations_to_data

CHUNK_SIZE = 16


# ---------------------------------------------------------------------------
# Persistent process pool — created once, reused for every job
# ---------------------------------------------------------------------------

_pool_lock = threading.Lock()
_pool: concurrent.futures.ProcessPoolExecutor | None = None
_pool_max_workers: int | None = None


def _worker_init() -> None:
    """
    Runs once per worker process, at pool creation time — NOT per job.
    Add anything with heavy import-time cost here (your ops modules
    included) so that cost is front-loaded into pool startup instead of
    the first task that happens to need it.
    """
    import numpy  # noqa: F401
    import scipy  # noqa: F401
    import tomopy  # noqa: F401  -- adjust to your actual heavy deps


def _get_process_pool() -> concurrent.futures.ProcessPoolExecutor:
    global _pool, _pool_max_workers
    if _pool is None:
        with _pool_lock:
            if _pool is None:  # re-check inside the lock (double-checked locking)
                _pool_max_workers = os.cpu_count() or 1
                _pool = concurrent.futures.ProcessPoolExecutor(
                    max_workers=_pool_max_workers,
                    mp_context=multiprocessing.get_context("spawn"),
                    initializer=_worker_init,
                )
                atexit.register(_pool.shutdown, wait=True, cancel_futures=True)
    return _pool


def shutdown_process_pool() -> None:
    """Optional: call from your app's shutdown hook for a clean exit sooner than atexit."""
    global _pool, _pool_max_workers
    with _pool_lock:
        if _pool is not None:
            _pool.shutdown(wait=True, cancel_futures=True)
            _pool = None
            _pool_max_workers = None


# ---------------------------------------------------------------------------
# Picklable descriptors — the only "handle" to a volume that crosses the
# process boundary. Never pass workspace / dataset_service themselves.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _MemmapDescriptor:
    path: str
    shape: tuple
    dtype: str  # stored as str, not np.dtype, to keep pickling trivial/stable
    mode: str = "r+"

    def open(self) -> np.memmap:
        return np.memmap(self.path, dtype=self.dtype, mode=self.mode, shape=self.shape)


def _volume_descriptor(workspace) -> _MemmapDescriptor:
    """
    workspace._volume is the same np.memmap object handed to
    export_data() at the end of the pipeline. Adjust attribute names
    here if your Workspace stores this differently.
    """
    vol = workspace._volume
    return _MemmapDescriptor(path=vol.filename, shape=vol.shape, dtype=str(vol.dtype))


def _source_descriptor(dataset_service) -> _MemmapDescriptor | None:
    """
    Best-effort: if the *loaded dataset* is itself memmap-backed and
    exposes the backing file, workers can read source projections with
    zero IPC, same as they do for the workspace volume. Returns None if
    that's not available — callers then fall back to having the parent
    read frames via dataset_service.get_projection(i) and ship the
    arrays into the worker instead (still correct, just some extra
    serialization on the input side).

    Adjust attribute names to match your actual DatasetService.
    """
    vol = getattr(dataset_service, "_volume", None)
    if isinstance(vol, np.memmap):
        return _MemmapDescriptor(path=vol.filename, shape=vol.shape, dtype=str(vol.dtype), mode="r")
    return None


# ---------------------------------------------------------------------------
# Worker-side functions. Top-level (not closures/methods) and pickled by
# reference under spawn — only their arguments are pickled by value, so
# every argument here must be cheap, simple, and side-effect-free to pickle.
# ---------------------------------------------------------------------------

def _process_projection_chunk_from_memmap(
    src: _MemmapDescriptor, dst: _MemmapDescriptor, proj_config, start: int, end: int
) -> int:
    src_vol, dst_vol = src.open(), dst.open()
    for i in range(start, end):
        processed, _ = apply_operations_to_data(src_vol[i], proj_config)
        dst_vol[i] = processed
    dst_vol.flush()
    return end - start


def _process_projection_chunk_from_frames(
    frames: list, dst: _MemmapDescriptor, proj_config, start: int
) -> int:
    """Fallback used when the source dataset isn't confirmed memmap-backed:
    the parent already read the raw frames and shipped them in."""
    dst_vol = dst.open()
    for offset, frame in enumerate(frames):
        processed, _ = apply_operations_to_data(frame, proj_config)
        dst_vol[start + offset] = processed
    dst_vol.flush()
    return len(frames)


def _process_sinogram_chunk(dst: _MemmapDescriptor, sino_config, start: int, end: int) -> int:
    dst_vol = dst.open()
    for y in range(start, end):
        sinogram = dst_vol[:, y, :]  # assumes (projection, height, width); adjust axis if different
        processed, _ = apply_operations_to_data(sinogram, sino_config)
        dst_vol[:, y, :] = processed
    dst_vol.flush()
    return end - start


def _copy_projection_chunk(src: _MemmapDescriptor, dst: _MemmapDescriptor, start: int, end: int) -> int:
    """No-ops pass-through copy. Only used when the source is confirmed
    memmap-backed (see execute_preprocessing_pipeline) — pure I/O, no CPU
    work, so it's only worth the process-pool round trip when it lets us
    skip shipping frame data through IPC entirely."""
    src_vol, dst_vol = src.open(), dst.open()
    dst_vol[start:end] = src_vol[start:end]
    dst_vol.flush()
    return end - start


# ---------------------------------------------------------------------------
# Parent-side scheduler: keeps a sliding window of chunks in flight across
# the persistent pool, so workers stay continuously fed while still giving
# the parent a checkpoint (after each chunk completes) to notice
# cancellation and stop feeding new work.
# ---------------------------------------------------------------------------

def _run_chunked_processes(
    job_id: str,
    job_manager: JobManager,
    total_items: int,
    submit_chunk: Callable[[concurrent.futures.Executor, int, int], concurrent.futures.Future],
    *,
    chunk_size: int = CHUNK_SIZE,
    total_steps: int | None = None,
    completed_ref: list | None = None,
    label: str = "",
    operation_name: str = "",
    check_cancellation: bool = False,
) -> bool:
    """
    submit_chunk(pool, start, end) must submit a worker task and return
    its Future; the Future's result() must be the number of items that
    chunk processed (used for progress accounting).

    Cancellation granularity is per-chunk (~chunk_size items), not
    per-item: a ProcessPoolExecutor can't preempt a task that's already
    running in a worker, so once a chunk starts it runs to completion.
    That's the trade-off for moving this from threads to processes; the
    parent still stops handing out *new* chunks the moment it notices
    the job was cancelled.

    Progress is reported once per completed chunk (not every 10 items —
    a chunk is already close to that granularity and it's the natural
    unit of feedback we get back from a process).

    Does NOT shut down the persistent pool on error — that pool is
    shared across all jobs for the app's lifetime. On a worker
    exception, not-yet-started chunks are best-effort cancelled and the
    exception is re-raised.
    """
    if total_items == 0:
        return False

    pool = _get_process_pool()
    in_flight_limit = max(1, (_pool_max_workers or os.cpu_count() or 1) * 2)
    if completed_ref is None:
        completed_ref = [0]

    chunk_bounds = iter((s, min(s + chunk_size, total_items)) for s in range(0, total_items, chunk_size))
    in_flight: dict = {}
    job_cancelled = False

    def submit_next() -> bool:
        bounds = next(chunk_bounds, None)
        if bounds is None:
            return False
        start, end = bounds
        in_flight[submit_chunk(pool, start, end)] = (start, end)
        return True

    for _ in range(in_flight_limit):
        if not submit_next():
            break

    try:
        while in_flight:
            done, _ = concurrent.futures.wait(in_flight, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                start, end = in_flight.pop(future)
                count = future.result()  # re-raises a worker exception here, in the parent

                if check_cancellation:
                    completed_ref[0] += count
                    progress = int((completed_ref[0] / total_steps) * 80)
                    job_manager.update_progress(
                        job_id, progress, f"{label}: {end}/{total_items}",
                        current_operation=operation_name,
                    )

            if check_cancellation and not job_cancelled:
                current_job = job_manager.get_job(job_id)
                if current_job and current_job.status == "cancelled":
                    job_cancelled = True

            if not job_cancelled:
                while len(in_flight) < in_flight_limit and submit_next():
                    pass
            # else: stop feeding new chunks; drain what's already in flight
    except Exception:
        for f in in_flight:
            f.cancel()  # best-effort; only affects chunks not yet started
        raise

    return job_cancelled


async def run_preprocessing_job(job_id: str) -> None:
    job_manager = get_job_manager()
    job = job_manager.start_job(job_id)
    if not job:
        return

    try:
        dataset_service = get_dataset_service()
        if not dataset_service.is_loaded():
            raise FileNotFoundError("No dataset loaded")

        proj_ops = [op for op in job.configuration.operations if op.enabled and op.scope in ("projection", "both")]
        sino_ops = [op for op in job.configuration.operations if op.enabled and op.scope == "sinogram"]

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(
                pool,
                execute_preprocessing_pipeline,
                job_id, job_manager, dataset_service, proj_ops, sino_ops,
            )

        job_manager.complete_job(job_id, "Full stack preprocessed successfully")

    except Exception as e:
        job_manager.fail_job(job_id, str(e))


def execute_preprocessing_pipeline(
    job_id: str,
    job_manager: JobManager,
    dataset_service: DatasetService,
    proj_ops: list[Operation],
    sino_ops: list[Operation],
) -> str:
    """
    Synchronous CPU worker running in the background thread pool.
    Scales preprocessing from 0% to 80% progress, and export streaming
    from 80% to 100%. Frame/slice CPU work is dispatched in chunks of
    CHUNK_SIZE to the persistent process pool (see module docstring).
    """
    metadata = dataset_service.get_metadata()
    num_projections = metadata["projection_count"]
    
    # --- DRY RUN FOR DYNAMIC SHAPES ---
    # Determine the post-projection dimensions to prevent NumPy broadcast errors
    # when operations like 'crop_pad_beam' alter the frame shape.
    test_frame = dataset_service.get_projection(0)
    if proj_ops:
        proj_config = PreprocessingConfiguration(operations=proj_ops)
        test_frame, _ = apply_operations_to_data(test_frame, proj_config)
        
    out_height, out_width = test_frame.shape
    num_slices = out_height  # Sinogram pass must iterate over the NEW height

    total_steps = (num_projections if proj_ops else 0) + (num_slices if sino_ops else 0)

    # Note: Ensure your dataset_service.create_workspace method accepts 
    # these dynamic shape overrides instead of relying on the original metadata.
    workspace = dataset_service.create_workspace(
        job_id, 
        shape=(num_projections, out_height, out_width)
    )
    dst = _volume_descriptor(workspace)
    completed_ref = [0]

    try:
        # Projection Operations Pass (Scaled to 0%-80% range)
        if proj_ops:
            # proj_config is already instantiated above in the dry run, but we 
            # instantiate again or just use the existing one to be safe.
            src = _source_descriptor(dataset_service)

            if src is not None:
                def submit_proj_chunk(pool, start, end):
                    return pool.submit(_process_projection_chunk_from_memmap, src, dst, proj_config, start, end)
            else:
                def submit_proj_chunk(pool, start, end):
                    frames = [dataset_service.get_projection(i) for i in range(start, end)]
                    return pool.submit(_process_projection_chunk_from_frames, frames, dst, proj_config, start)

            cancelled = _run_chunked_processes(
                job_id, job_manager, num_projections, submit_proj_chunk,
                total_steps=total_steps, completed_ref=completed_ref,
                label="Projection pass", operation_name="projection_pass",
                check_cancellation=True,
            )
            if cancelled:
                return ""
            workspace.flush()
        else:
            src = _source_descriptor(dataset_service)
            if src is not None:
                def submit_copy_chunk(pool, start, end):
                    return pool.submit(_copy_projection_chunk, src, dst, start, end)
                _run_chunked_processes(job_id, job_manager, num_projections, submit_copy_chunk)
            else:
                for i in range(num_projections):
                    workspace.write_projection(i, dataset_service.get_projection(i))
            workspace.flush()

        # Sinogram Operations Pass (Scaled to 0%-80% range)
        if sino_ops:
            sino_config = PreprocessingConfiguration(operations=sino_ops)

            def submit_sino_chunk(pool, start, end):
                return pool.submit(_process_sinogram_chunk, dst, sino_config, start, end)

            cancelled = _run_chunked_processes(
                job_id, job_manager, num_slices, submit_sino_chunk,
                total_steps=total_steps, completed_ref=completed_ref,
                label="Sinogram pass", operation_name="sinogram_pass",
                check_cancellation=True,
            )
            if cancelled:
                return ""
            workspace.flush()

        # Set progress to 80% threshold before initiating export streaming
        job_manager.update_progress(
            job_id, 80, "Preprocessing complete. Preparing file export...",
            current_operation="export_pass",
        )

        # Export Pass (Scaled to 80%-100% range)
        export_service = ExportService(output_dir=f"./data/exports/{job_id}")
        export_path = export_service.export_data(
            workspace_volume=workspace._volume,
            filename="preprocessed_volume",
            export_format=metadata["format"],
            job_id=job_id,
            job_manager=job_manager,
        )

        current_job = job_manager.get_job(job_id)
        if current_job and current_job.status == "cancelled":
            return ""

        if not export_service.verify_export(export_path):
            raise RuntimeError(f"Export verification failed for file at {export_path}")

        return export_path

    finally:
        workspace.close()


# Optional: call this once from your app's startup hook (e.g. a FastAPI
# lifespan handler) so the pool is already warm before the first real job
# arrives, instead of the first job silently eating the spawn/import cost.
#
#   @app.on_event("startup")
#   def _warm_pool():
#       _get_process_pool()