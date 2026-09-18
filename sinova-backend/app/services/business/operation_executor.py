"""
Operation execution engine.

Applies preprocessing operations to image data in the correct order,
respecting dependencies. Each operation is simple to understand and test.

Preview and full-stack processing both call apply_operations_to_data with
the same PreprocessingConfiguration -- there is no separate "preview
version" of any operation.

Operations whose parameters depend on more than the currently selected
slice (currently just COR estimation) are NOT resolved here. That happens
once, up front, via resolve_broad_scope_operation() -- by the time a
configuration reaches apply_operations_to_data, every parameter is already
a concrete, slice-applicable value.
"""
import asyncio
import concurrent.futures
from typing import Any
import os

import numpy as np

from app.schemas.preprocessing import DataContext, Operation, PreprocessingConfiguration
from app.services.business.job_manager import JobManager, get_job_manager
from app.services.processing import preprocessing_ops
from app.services.business.dataset_access import DatasetService, get_dataset_service
from app.services.business.export_service import ExportService

dataset_service = get_dataset_service()


def apply_single_operation(
    data: np.ndarray, operation: Operation
) -> tuple[np.ndarray, Operation]:
    """Apply a single preprocessing operation to an array using configured parameters."""
    if not operation.enabled:
        return data, operation

    short_name = operation.short_name
    params = operation.parameters

    if short_name == "normalize":
        flat_param = params.get("flat")
        dark_param = params.get("dark")
        dataset_service = get_dataset_service()

        flat_path = str(flat_param) if flat_param and str(flat_param).lower() != "auto" else None
        dark_path = str(dark_param) if dark_param and str(dark_param).lower() != "auto" else None

        if flat_path or dark_path:
            dataset_service.load_normalization(flat_path=flat_path, dark_path=dark_path)

        flat_ref = None
        if dataset_service.flat_reader is not None:
            flat_ref = dataset_service.flat_reader.get_data()
        elif getattr(dataset_service, "reader", None) and hasattr(dataset_service.reader, "get_flat"):
            flat_ref = dataset_service.reader.get_flat()

        dark_ref = None
        if dataset_service.dark_reader is not None:
            dark_ref = dataset_service.dark_reader.get_data()
        elif getattr(dataset_service, "reader", None) and hasattr(dataset_service.reader, "get_dark"):
            dark_ref = dataset_service.reader.get_dark()

        data = preprocessing_ops.normalize(data, flat=flat_ref, dark=dark_ref)

        if params.get("logarithm", False):
            data = preprocessing_ops.negative_log(data)

        return data, operation

    elif short_name == "negative_log":
        epsilon = params.get("epsilon", 1e-8)
        return preprocessing_ops.negative_log(data, epsilon), operation

    elif short_name == "clip_attenuation":
        max_value = params.get("max_value", params.get("threshold", 1.0))
        mode = params.get("mode", "Auto")
        return preprocessing_ops.clip_attenuation(data, max_value=max_value, mode=mode), operation

    elif short_name == "denoise":
        method = params.get("method", "median")
        if method == "median":
            kernel_size = params.get("kernel_size", 3)
            return preprocessing_ops.denoise_median(data, kernel_size), operation
        elif method == "gaussian":
            sigma = params.get("sigma", 1.0)
            return preprocessing_ops.denoise_gaussian(data, sigma), operation
        else:
            raise ValueError(f"Unknown denoise method: {method}")

    elif short_name == "fov_mask":
        radius = params.get("radius", params.get("margin", 0.95))
        center_x = params.get("center_x")
        center_y = params.get("center_y")

        cx = float(center_x) if center_x else None
        cy = float(center_y) if center_y else None
        rad = float(radius) if radius else None

        data = preprocessing_ops.apply_fov_mask(
            data, center_x=cx, center_y=cy, radius=rad
        )
        return data, operation

    elif short_name == "crop_pad_beam":
        pad = int(params.get("pad", 128))
        navg = int(params.get("navg", 8))
        beam_mask = params.get("beam_mask", data > 0)
        current_cor = float(
            params.get("rot_center", params.get("offset", params.get("value", 0.0)))
        )

        data, updated_cor, (y0, y1) = preprocessing_ops.crop_pad_beam(
            data=data,
            beam=beam_mask,
            rot_center=current_cor,
            pad=pad,
            navg=navg,
        )

        params["rot_center"] = updated_cor
        params["crop_y"] = (y0, y1)

        dataset_service = get_dataset_service()
        dataset_service.update_geometry_bounds(rot_center=updated_cor, crop_y=(y0, y1))

        return data, operation
    
    elif short_name == "mutate":
        auto = params.get("auto", True)
        if auto == False:
            new_count = int(params.get("new_count", 0))
            data = preprocessing_ops.mutate_projections(data, auto=False, new_count=new_count)
        elif auto == True:
            data = preprocessing_ops.mutate_projections(data, auto=True)
        else:
            raise ValueError(f"Unknown mutate mode: {auto}")
        
        params["new_count"] = data.shape[0]  # Update the new_count parameter to reflect the actual number of projections after mutation

        return data, operation

    elif short_name == "cor_shift":
        is_estimating = params.get("cor_estimation")

        if is_estimating:
            estimated_cor = preprocessing_ops.find_cor_vo(data)
            params["value"] = float(estimated_cor)
            params["cor_estimation"] = False
            if "cor-estimation" in params:
                params["cor-estimation"] = False

        return data, operation
    
    # DESTRIPING OPERATIONS
    elif short_name == "ring_filter_fw":
        level = int(params.get("level", 5))
        sigma = float(params.get("sigma", params.get("parameter", 2.0)))

        data = preprocessing_ops.ring_filter_fw(data, level=level, sigma=sigma)
        return data, operation

    elif short_name == "ring_filter_vo":
        window = int(params.get("window", 21))

        data = preprocessing_ops.ring_filter_vo(data, size=window)
        return data, operation

    else:
        raise ValueError(f"Unknown operation: {short_name}")


def apply_operations_to_data(
    data: np.ndarray,
    configuration: PreprocessingConfiguration,
) -> tuple[np.ndarray, PreprocessingConfiguration]:
    """
    Apply all enabled operations to data in order.
    """
    result = data.astype(np.float32)

    for i, operation in enumerate(configuration.operations):
        if operation.enabled:
            try:
                result, updated_operation = apply_single_operation(result, operation)
                configuration.operations[i] = updated_operation
            except Exception as e:
                raise ValueError(
                    f"Failed to apply operation '{operation.name}': {str(e)}"
                ) from e

    return result, configuration

# async def run_preprocessing_job(job_id: str) -> None:
#     job_manager = get_job_manager()
#     job = job_manager.start_job(job_id)
#     if not job:
#         return

#     try:
#         dataset_service = get_dataset_service()
#         if not dataset_service.is_loaded():
#             raise FileNotFoundError("No dataset loaded")

#         proj_ops = [op for op in job.configuration.operations if op.enabled and op.scope in ("projection", "both")]
#         sino_ops = [op for op in job.configuration.operations if op.enabled and op.scope == "sinogram"]

#         loop = asyncio.get_running_loop()
#         with concurrent.futures.ThreadPoolExecutor() as pool:
#             await loop.run_in_executor(
#                 pool,
#                 execute_preprocessing_pipeline,
#                 job_id, job_manager, dataset_service, proj_ops, sino_ops
#             )

#         job_manager.complete_job(job_id, "Full stack preprocessed successfully")

#     except Exception as e:
#         job_manager.fail_job(job_id, str(e))


# def _run_parallel_pass(
#     process_pool: concurrent.futures.ProcessPoolExecutor,
#     max_workers: int,
#     count: int,
#     config: "PreprocessingConfiguration",
#     read_item,
#     write_item,
#     job_manager: "JobManager",
#     job_id: str,
#     total_steps: int,
#     completed_before: int,
#     label: str,
#     op_name: str,
# ) -> tuple[bool, int]:
#     """
#     Fans `count` independent items out across process_pool (real, separate
#     cores), keeping at most 2 * max_workers in flight. I/O (read_item /
#     write_item) and cancellation/progress checks stay on the calling thread.
#     Returns (was_cancelled, items_completed).
#     """
#     window = max(1, max_workers * 2)
#     pending: dict[concurrent.futures.Future, int] = {}
#     next_idx = 0
#     done = 0

#     def top_up() -> None:
#         nonlocal next_idx
#         while next_idx < count and len(pending) < window:
#             fut = process_pool.submit(apply_operations_to_data, read_item(next_idx), config)
#             pending[fut] = next_idx
#             next_idx += 1

#     top_up()

#     while pending:
#         current_job = job_manager.get_job(job_id)
#         if current_job and current_job.status == "cancelled":
#             for fut in pending:
#                 fut.cancel()
#             return True, done

#         finished, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
#         for fut in finished:
#             idx = pending.pop(fut)
#             processed_item, _ = fut.result()
#             write_item(idx, processed_item)
#             done += 1

#             if done == 1 or done % 10 == 0 or done == count:
#                 progress = int(((completed_before + done) / total_steps) * 80)
#                 job_manager.update_progress(
#                     job_id, progress, f"{label}: {done}/{count}", current_operation=op_name,
#                 )
#         top_up()

#     return False, done


# def execute_preprocessing_pipeline(
#     job_id: str,
#     job_manager: "JobManager",
#     dataset_service: "DatasetService",
#     proj_ops: list["Operation"],
#     sino_ops: list["Operation"],
# ) -> str:
#     """
#     Synchronous orchestrator running in a background thread (kept off the
#     event loop). Per-frame/per-slice work is farmed out to a
#     ProcessPoolExecutor so it runs on real, separate cores.
#     Scales preprocessing from 0% to 80% progress, and export streaming from 80% to 100%.
#     """
#     metadata = dataset_service.get_metadata()
#     num_projections = metadata["projection_count"]
#     num_slices = metadata["height"]
#     total_steps = (num_projections if proj_ops else 0) + (num_slices if sino_ops else 0)
#     completed = 0

#     workspace = dataset_service.create_workspace(job_id)
#     max_workers = os.cpu_count() or 1

#     try:
#         with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as process_pool:
#             # Projection Operations Pass (Scaled to 0%-80% range)
#             if proj_ops:
#                 proj_config = PreprocessingConfiguration(operations=proj_ops)
#                 cancelled, done = _run_parallel_pass(
#                     process_pool, max_workers, num_projections, proj_config,
#                     dataset_service.get_projection, workspace.write_projection,
#                     job_manager, job_id, total_steps, completed,
#                     "Projection pass", "projection_pass",
#                 )
#                 completed += done
#                 if cancelled:
#                     return ""
#                 workspace.flush()
#             else:
#                 for i in range(num_projections):
#                     workspace.write_projection(i, dataset_service.get_projection(i))
#                 workspace.flush()

#             # Sinogram Operations Pass (Scaled to 0%-80% range)
#             if sino_ops:
#                 sino_config = PreprocessingConfiguration(operations=sino_ops)
#                 cancelled, done = _run_parallel_pass(
#                     process_pool, max_workers, num_slices, sino_config,
#                     workspace.read_sinogram, workspace.write_sinogram,
#                     job_manager, job_id, total_steps, completed,
#                     "Sinogram pass", "sinogram_pass",
#                 )
#                 completed += done
#                 if cancelled:
#                     return ""
#                 workspace.flush()

#         # Set progress to 80% threshold before initiating export streaming
#         job_manager.update_progress(
#             job_id, 80, "Preprocessing complete. Preparing file export...",
#             current_operation="export_pass",
#         )

#         # Export Pass (Scaled to 80%-100% range)
#         export_service = ExportService(output_dir=f"./data/exports/{job_id}")
#         export_path = export_service.export_data(
#             workspace_volume=workspace._volume,
#             filename="preprocessed_volume",
#             export_format=metadata["format"],
#             job_id=job_id,
#             job_manager=job_manager,
#         )

#         current_job = job_manager.get_job(job_id)
#         if current_job and current_job.status == "cancelled":
#             return ""

#         if not export_service.verify_export(export_path):
#             raise RuntimeError(f"Export verification failed for file at {export_path}")

#         return export_path

#     finally:
#         workspace.close()