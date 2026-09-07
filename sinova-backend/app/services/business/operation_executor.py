"""
Operation execution engine.

Applies preprocessing operations to image data in the correct order,
respecting dependencies. Each operation is simple to understand and test.
"""
import numpy as np

from app.schemas.preprocessing import Operation, PreprocessingConfiguration
from app.services.processing import preprocessing_ops


def apply_single_operation(data: np.ndarray, operation: Operation) -> np.ndarray:
    """
    Apply a single preprocessing operation to an array.

    Args:
        data: Input image data
        operation: The operation to apply

    Returns:
        Processed image data

    Raises:
        ValueError: If operation is unknown or parameters are invalid
    """
    if not operation.enabled:
        return data

    short_name = operation.short_name
    params = operation.parameters

    # Intensity operations
    if short_name == "normalize":
        vmin = params.get("vmin")
        vmax = params.get("vmax")
        return preprocessing_ops.normalize(data, vmin, vmax)

    elif short_name == "negative_log":
        epsilon = params.get("epsilon", 1e-8)
        return preprocessing_ops.negative_log(data, epsilon)

    elif short_name == "clip_attenuation":
        max_value = params.get("max_value", 1.0)
        return preprocessing_ops.clip_attenuation(data, max_value)

    # Spatial operations
    elif short_name == "denoise":
        method = params.get("method", "median")
        if method == "median":
            kernel_size = params.get("kernel_size", 3)
            return preprocessing_ops.denoise_median(data, kernel_size)
        elif method == "gaussian":
            sigma = params.get("sigma", 1.0)
            return preprocessing_ops.denoise_gaussian(data, sigma)
        else:
            raise ValueError(f"Unknown denoise method: {method}")

    elif short_name == "fov_mask":
        radius = params.get("radius", 0.95)
        return preprocessing_ops.apply_fov_mask(data, radius)

    # Geometry operations
    elif short_name == "cor":
        # COR is a horizontal shift
        cor_offset = params.get("offset", 0.0)
        return preprocessing_ops.apply_cor_shift(data, cor_offset)

    # Ring/destriping operations
    elif short_name == "ring_filter":
        # Placeholder for ring filtering
        # Real implementation would use Fourier-based destriping
        return data

    else:
        raise ValueError(f"Unknown operation: {short_name}")


def apply_operations_to_data(
    data: np.ndarray,
    configuration: PreprocessingConfiguration,
) -> np.ndarray:
    """
    Apply all enabled operations to data in order.

    Operations are applied in the order they appear in the configuration.
    Dependencies are assumed to be handled by validation before this point.

    Args:
        data: Input image data
        configuration: Preprocessing configuration with operations

    Returns:
        Processed image data

    Raises:
        ValueError: If any operation fails
    """
    result = data.astype(np.float32)

    for operation in configuration.operations:
        if operation.enabled:
            try:
                result = apply_single_operation(result, operation)
            except Exception as e:
                raise ValueError(
                    f"Failed to apply operation '{operation.name}': {str(e)}"
                ) from e

    return result
