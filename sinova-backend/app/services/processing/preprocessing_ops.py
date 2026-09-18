import numpy as np
from scipy import ndimage

import tomopy

def normalize(
    data: np.ndarray,
    flat: np.ndarray | float | None = None,
    dark: np.ndarray | float | None = None,
    is_sinogram: bool = False,
) -> np.ndarray:
    """Normalize projection or sinogram data strictly using TomoPy."""
    data = data.astype(np.float32)

    flat_val = 1.0 if flat is None else flat
    dark_val = 0.0 if dark is None else dark

    # Average 3D flat/dark stacks (N_frames, Y, Z) down to 2D (Y, Z)
    if isinstance(flat_val, np.ndarray) and flat_val.ndim == 3:
        flat_val = np.mean(flat_val, axis=0)
    if isinstance(dark_val, np.ndarray) and dark_val.ndim == 3:
        dark_val = np.mean(dark_val, axis=0)

    # If input is a sinogram (Angles, Width), collapse 2D flat/dark (Height, Width) to 1D profile (Width,)
    if is_sinogram or (
        data.ndim == 2
        and isinstance(flat_val, np.ndarray)
        and flat_val.ndim == 2
        and data.shape[0] != flat_val.shape[0]
    ):
        if isinstance(flat_val, np.ndarray) and flat_val.ndim == 2:
            flat_val = np.mean(flat_val, axis=0)
        if isinstance(dark_val, np.ndarray) and dark_val.ndim == 2:
            dark_val = np.mean(dark_val, axis=0)

    if data.ndim == 2:
        data_3d = data[np.newaxis, :, :]

        if isinstance(flat_val, np.ndarray):
            if flat_val.ndim == 1:
                flat_3d = flat_val[np.newaxis, np.newaxis, :]
            elif flat_val.ndim == 2:
                flat_3d = flat_val[np.newaxis, :, :]
            else:
                flat_3d = flat_val
        else:
            flat_3d = np.full_like(data_3d, flat_val)

        if isinstance(dark_val, np.ndarray):
            if dark_val.ndim == 1:
                dark_3d = dark_val[np.newaxis, np.newaxis, :]
            elif dark_val.ndim == 2:
                dark_3d = dark_val[np.newaxis, :, :]
            else:
                dark_3d = dark_val
        else:
            dark_3d = np.full_like(data_3d, dark_val)

        res = tomopy.normalize(data_3d, flat_3d, dark_3d)
        return res[0].astype(np.float32)

    flat_arr = flat_val if isinstance(flat_val, np.ndarray) else np.full_like(data, flat_val)
    dark_arr = dark_val if isinstance(dark_val, np.ndarray) else np.full_like(data, dark_val)
    return tomopy.normalize(data, flat_arr, dark_arr).astype(np.float32)

def negative_log(data: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
    """Apply safe negative logarithm transformation."""
    clamped = np.clip(data, epsilon, 1.0)
    return -np.log(clamped).astype(np.float32)


def denoise_median(data: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply Median Filter for smoothing."""
    if kernel_size % 2 == 0:
        kernel_size += 1

    # Ensure kernel size is at least 1
    is_2d = data.ndim == 2
    # Expand 2D array (H, W) -> 3D (1, H, W) for TomoPy
    stacked = data[np.newaxis, :, :] if is_2d else data
    
    filtered = tomopy.misc.corr.median_filter(stacked, size=kernel_size).astype(np.float32)
    
    return filtered[0] if is_2d else filtered

def denoise_gaussian(data: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian blur for smoothing."""
    is_2d = data.ndim == 2
    # Expand 2D (H, W) -> 3D (1, H, W) for TomoPy
    stacked = data[np.newaxis, :, :] if is_2d else data
    filtered = tomopy.misc.corr.gaussian_filter(stacked, sigma=sigma).astype(
        np.float32
    )
    return filtered[0] if is_2d else filtered

import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit


def mutate_projections(
    data: np.ndarray,
    auto: bool = True,
    new_count: int | None = None,
) -> np.ndarray:
    """Trim or resample sinogram projections to cover exactly one full 360 degree rotation."""
    data = data.astype(np.float32)
    n_frames, width = data.shape

    if auto:
        air_baseline = np.percentile(data, 95, axis=1, keepdims=True)
        signal = np.clip(air_baseline - data, 0, None)

        x_coords = np.arange(width)
        com = (signal * x_coords).sum(axis=1) / (signal.sum(axis=1) + 1e-8)

        com_centered = com - com.mean()
        fft_spectrum = np.abs(np.fft.rfft(com_centered * np.hanning(n_frames)))
        k_peak = np.argmax(fft_spectrum[1:]) + 1
        t0_est = n_frames / k_peak

        def sine_model(n, amplitude, period, phase, offset):
            return amplitude * np.sin(2 * np.pi * n / period + phase) + offset

        p0 = [com_centered.std() * np.sqrt(2), t0_est, 0.0, com.mean()]

        try:
            popt, _ = curve_fit(sine_model, np.arange(n_frames), com, p0=p0)
            # Extracted period T represents frames per single 360 degree rotation
            target_count = int(np.round(popt[1]))
        except RuntimeError:
            target_count = new_count if new_count is not None else n_frames
    elif auto is False:
        if new_count is None:
            raise ValueError("new_count must be provided when auto is set to False.")
        target_count = new_count

    # If dataset spans 1 rotation or less, leave projections unmodified
    if target_count >= n_frames or target_count <= 0:
        return data

    old_grid = np.linspace(0, 1, n_frames)
    new_grid = np.linspace(0, 1, target_count)
    interpolator = interp1d(old_grid, data, axis=0, kind="linear")

    return interpolator(new_grid).astype(np.float32)


def apply_fov_mask(
    data: np.ndarray,
    center_x: float | None = None,
    center_y: float | None = None,
    radius: float | None = None,
) -> np.ndarray:
    """Apply circular FOV mask based on explicit center coordinates and radius."""
    height, width = data.shape[-2:]

    if center_x is None:
        center_x = (width - 1) / 2.0
    if center_y is None:
        center_y = (height - 1) / 2.0
    if radius is None:
        radius = min(height, width) * 0.95 / 2.0

    y, x = np.ogrid[:height, :width]
    mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2

    if data.ndim == 3:
        mask = mask[np.newaxis, :, :]

    return (data * mask).astype(np.float32)


def find_cor_vo(
    data: np.ndarray,
    smin: int = -50,
    smax: int = 50,
    srad: float = 6.0,
    step: float = 0.25,
    ratio: float = 0.5,
    drop: int = 20,
) -> float:
    """Compute Center of Rotation (COR) using Vo's method via TomoPy."""
    if tomopy is None:
        height, width = data.shape[-2:]
        return float((width - 1) / 2.0)

    if data.ndim == 2:
        tomo_3d = data[np.newaxis, :, :]
    else:
        tomo_3d = data

    center = tomopy.find_center_vo(
        tomo_3d,
        smin=smin,
        smax=smax,
        srad=srad,
        step=step,
        ratio=ratio,
        drop=drop,
    )
    return float(center)


def ring_filter_fw(
    data: np.ndarray,
    level: int = 5,
    sigma: float = 2.0,
    wname: str = "db5",
) -> np.ndarray:
    """Remove ring artifacts using TomoPy's Fourier-Wavelet stripe removal."""
    if tomopy is None:
        return data.astype(np.float32)

    is_2d = data.ndim == 2
    stacked = data[np.newaxis, :, :] if is_2d else data

    res = tomopy.prep.stripe.remove_stripe_fw(
        stacked,
        level=level,
        wname=wname,
        sigma=sigma,
    ).astype(np.float32)

    return res[0] if is_2d else res


def ring_filter_vo(
    data: np.ndarray,
    size: int = 21,
) -> np.ndarray:
    """Remove ring artifacts using TomoPy's Vo sorting-based stripe removal."""
    if tomopy is None:
        return data.astype(np.float32)

    is_2d = data.ndim == 2
    stacked = data[np.newaxis, :, :] if is_2d else data

    res = tomopy.prep.stripe.remove_stripe_based_sorting(
        stacked,
        size=size,
    ).astype(np.float32)

    return res[0] if is_2d else res


def clip_attenuation(
    data: np.ndarray, max_value: float | None = None, mode: str = "Auto"
) -> np.ndarray:
    """Clip attenuation values to prevent negative log artifacts."""
    if max_value is None:
        max_value = 1.0
    
    LO = 1e-6
    HI = max_value
    valid_data = data[data > 0]
    
    if mode == "Auto":
        LO = np.percentile(valid_data, 1)
        HI = np.percentile(valid_data, 99.5)

    return np.clip(data, LO, HI).astype(np.float32)

def crop_pad_beam(
    data: np.ndarray,
    beam: np.ndarray,
    rot_center: float,
    pad: int = 128,
    navg: int = 8,
) -> tuple[np.ndarray, float, tuple[int, int]]:
    """
    Crop projection to the active beam bounding box and extend rows horizontally
    with a cosine roll-off to zero to mitigate truncation artifacts.

    Args:
        data: 2D (H, W) or 3D (N, H, W) array of projections
        beam: 2D (H, W) boolean mask representing beam illumination
        rot_center: Current horizontal center of rotation
        pad: Width of the cosine roll-off padding in pixels
        navg: Number of inner edge pixels to average for the fill level

    Returns:
        Tuple of (padded_data, updated_rot_center, (y0, y1))
    """
    if not beam.any():
        return data.astype(np.float32), float(rot_center), (0, data.shape[-2])

    is_2d = data.ndim == 2
    proj = data[np.newaxis, :, :] if is_2d else data

    ys = np.where(beam.any(axis=1))[0]
    xs = np.where(beam.any(axis=0))[0]
    y0, y1 = int(ys[0]), int(ys[-1] + 1)
    x0, x1 = int(xs[0]), int(xs[-1] + 1)

    m = beam[y0:y1, x0:x1]
    h, w = m.shape
    num_projs = proj.shape[0]

    out = np.zeros((num_projs, h, w + 2 * pad), dtype=np.float32)
    out[:, :, pad : pad + w] = proj[:, y0:y1, x0:x1] * m

    u = np.arange(-pad, w + pad)
    for i in range(h):
        v = np.where(m[i])[0]
        if v.size < navg:
            continue
        a, b = int(v[0]), int(v[-1])

        # Apply left and right edge cosine roll-off
        for val, d in (
            (out[:, i, pad + a : pad + a + navg].mean(axis=1), a - u),
            (out[:, i, pad + b - navg + 1 : pad + b + 1].mean(axis=1), u - b),
        ):
            k = d > 0
            if np.any(k):
                out[:, i, k] = val[:, None] * 0.5 * (
                    1 + np.cos(np.pi * np.clip(d[k] / pad, 0, 1))
                )

    updated_rot_center = float(rot_center) - x0 + pad
    result = out[0] if is_2d else out

    return result.astype(np.float32), updated_rot_center, (y0, y1)