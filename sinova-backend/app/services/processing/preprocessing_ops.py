import numpy as np
from scipy import ndimage

try:
    import tomopy
except ModuleNotFoundError:
    tomopy = None


def normalize(
    data: np.ndarray,
    flat: np.ndarray | float | None = None,
    dark: np.ndarray | float | None = None,
) -> np.ndarray:
    """Normalize projection data using TomoPy or NumPy with flat and dark references."""
    data = data.astype(np.float32)

    if flat is None:
        flat = 1.0
    if dark is None:
        dark = 0.0

    # Reduce 3D reference stacks to 2D mean frames
    if isinstance(flat, np.ndarray) and flat.ndim == 3:
        flat = np.mean(flat, axis=0)
    if isinstance(dark, np.ndarray) and dark.ndim == 3:
        dark = np.mean(dark, axis=0)

    # Handle 2D sinograms where data shape is (projections, width)
    if (
        data.ndim == 2
        and isinstance(flat, np.ndarray)
        and flat.ndim == 2
        and data.shape[1] == flat.shape[1]
        and data.shape[0] != flat.shape[0]
    ):
        flat = np.mean(flat, axis=0)

    if (
        data.ndim == 2
        and isinstance(dark, np.ndarray)
        and dark.ndim == 2
        and data.shape[1] == dark.shape[1]
        and data.shape[0] != dark.shape[0]
    ):
        dark = np.mean(dark, axis=0)

    # TomoPy execution path
    if tomopy is not None:
        if data.ndim == 2:
            data_3d = data[np.newaxis, :, :]

            if isinstance(flat, np.ndarray):
                flat_3d = (
                    flat[np.newaxis, :, :]
                    if flat.ndim == 2
                    else flat[np.newaxis, np.newaxis, :]
                )
            else:
                flat_3d = flat

            if isinstance(dark, np.ndarray):
                dark_3d = (
                    dark[np.newaxis, :, :]
                    if dark.ndim == 2
                    else dark[np.newaxis, np.newaxis, :]
                )
            else:
                dark_3d = dark

            res = tomopy.normalize(data_3d, flat_3d, dark_3d)
            return res[0].astype(np.float32)

        return tomopy.normalize(data, flat, dark).astype(np.float32)

    # NumPy fallback
    flat_val = flat.astype(np.float32) if isinstance(flat, np.ndarray) else flat
    dark_val = dark.astype(np.float32) if isinstance(dark, np.ndarray) else dark

    denom = np.maximum(flat_val - dark_val, 1e-8)
    normalized = (data - dark_val) / denom
    return np.clip(normalized, 0.0, None).astype(np.float32)


def negative_log(data: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
    """Apply safe negative logarithm transformation."""
    clamped = np.clip(data, epsilon, 1.0)
    return -np.log(clamped).astype(np.float32)


def denoise_median(data: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply Median Filter for smoothing."""
    if kernel_size % 2 == 0:
        kernel_size += 1

    if tomopy is not None:
        return tomopy.prep.median_filter(data, size=kernel_size).astype(
            np.float32
        )
    return ndimage.median_filter(data, size=kernel_size).astype(np.float32)


def denoise_gaussian(data: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian blur for smoothing."""
    if tomopy is not None:
        return tomopy.prep.gaussian_filter(data, sigma=sigma).astype(
            np.float32
        )
    return ndimage.gaussian_filter(data, sigma=sigma).astype(np.float32)


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


def apply_cor_shift(data: np.ndarray, cor_offset: float) -> np.ndarray:
    """Apply Center of Rotation (COR) correction shift."""
    if abs(cor_offset) < 0.01:
        return data.astype(np.float32)

    shift_int = int(round(cor_offset))

    if data.ndim == 2:
        return np.roll(data, shift_int, axis=1).astype(np.float32)
    elif data.ndim == 3:
        return np.roll(data, shift_int, axis=2).astype(np.float32)

    return data.astype(np.float32)


def ring_filter(data: np.ndarray, parameter: float = 0.1) -> np.ndarray:
    """Remove ring artifacts using TomoPy's Fourier-Wavelet stripe removal."""
    if tomopy is None:
        return data.astype(np.float32)

    return tomopy.prep.stripe.remove_stripe_fw(
        data,
        level=5,
        wname="db5",
        sigma=parameter * 2,
    ).astype(np.float32)


def clip_attenuation(
    data: np.ndarray, max_value: float | None = None
) -> np.ndarray:
    """Clip attenuation values to prevent negative log artifacts."""
    if max_value is None:
        max_value = 1.0

    return np.clip(data, 1e-6, max_value).astype(np.float32)

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