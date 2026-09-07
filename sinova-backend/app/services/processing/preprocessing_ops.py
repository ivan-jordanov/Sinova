import numpy as np
from scipy import ndimage

try:
    import tomopy
except ModuleNotFoundError:
    tomopy = None


def normalize(
    data: np.ndarray,
    vmin: float | None = None,
    vmax: float | None = None,
) -> np.ndarray:
    """Normalize array to 0-1 range using min-max scaling."""
    if vmin is None:
        vmin = float(np.min(data))
    if vmax is None:
        vmax = float(np.max(data))

    if vmax == vmin:
        return np.zeros_like(data, dtype=np.float32)

    normalized = (data.astype(np.float32) - vmin) / (vmax - vmin)
    return np.clip(normalized, 0.0, 1.0)


def negative_log(data: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
    """Apply safe negative logarithm transformation."""
    clamped = np.clip(data, epsilon, 1.0)
    return -np.log(clamped).astype(np.float32)


def denoise_median(data: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply TomoPy's Median Filter for smoothing."""
    if kernel_size % 2 == 0:
        kernel_size += 1

    if tomopy is not None:
        return tomopy.prep.median_filter(data, size=kernel_size).astype(np.float32)
    return ndimage.median_filter(data, size=kernel_size).astype(np.float32)


def denoise_gaussian(data: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply TomoPy's Gaussian blur for smoothing."""
    if tomopy is not None:
        return tomopy.prep.gaussian_filter(data, sigma=sigma).astype(np.float32)
    return ndimage.gaussian_filter(data, sigma=sigma).astype(np.float32)


def apply_fov_mask(data: np.ndarray, radius: float | None = None) -> np.ndarray:
    """Apply circular FOV mask using TomoPy's native circ_mask."""
    ratio = 0.95 if radius is None else radius
    
    if tomopy is not None and data.ndim == 2:
        # TomoPy expects 3D arrays for circ_mask (num_angles, height, width)
        data_3d = data[np.newaxis, :, :]
        masked = tomopy.circ_mask(data_3d, axis=0, ratio=ratio)
        return masked[0].astype(np.float32)
    
    elif tomopy is not None and data.ndim == 3:
        return tomopy.circ_mask(data, axis=0, ratio=ratio).astype(np.float32)

    if data.ndim in (2, 3):
        height, width = data.shape[-2:]
        y, x = np.ogrid[:height, :width]
        center_y = (height - 1) / 2
        center_x = (width - 1) / 2
        radius_pixels = min(height, width) * ratio / 2
        mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius_pixels**2
        return (data * mask).astype(np.float32)

    return data.astype(np.float32)


def apply_cor_shift(data: np.ndarray, cor_offset: float) -> np.ndarray:
    """
    Apply Center of Rotation (COR) correction via horizontal shift.
    Uses pure NumPy integer rolling to avoid external dependencies.
    """
    if abs(cor_offset) < 0.01:
        return data.astype(np.float32)

    shift_int = int(round(cor_offset))
    
    if data.ndim == 2:
        return np.roll(data, shift_int, axis=1).astype(np.float32)
    elif data.ndim == 3:
        return np.roll(data, shift_int, axis=2).astype(np.float32)
        
    return data.astype(np.float32)


def ring_filter(data: np.ndarray, parameter: float = 0.1) -> np.ndarray:
    """
    Remove ring artifacts using TomoPy's Fourier-Wavelet stripe removal.
    """
    if tomopy is None:
        return data.astype(np.float32)

    return tomopy.prep.stripe.remove_stripe_fw(
        data,
        level=5,
        wname="db5",
        sigma=parameter * 2,
    ).astype(np.float32)


def clip_attenuation(data: np.ndarray, max_value: float | None = None) -> np.ndarray:
    """Clip attenuation values to prevent negative log artifacts."""
    if max_value is None:
        max_value = 1.0

    return np.clip(data, 0.0, max_value).astype(np.float32)