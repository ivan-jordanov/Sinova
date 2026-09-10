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
from typing import Any

import numpy as np

from app.schemas.preprocessing import DataContext, Operation, PreprocessingConfiguration
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
        max_value = params.get("threshold", 1.0)
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

    elif short_name == "edge_enhance":
        # STILL INCOMPLETE: declared as an available operation (and has a
        # dependency on "denoise") but preprocessing_ops.py has no
        # implementation yet. Raise clearly instead of silently passing
        # data through -- a silent no-op would look like it worked.
        raise NotImplementedError(
            "Edge Enhance has no implementation yet in preprocessing_ops.py"
        )

    # Geometry operations
    elif short_name == "cor":
        # By this point `offset` is always a concrete number -- either the
        # user typed it in, or resolve_broad_scope_operation() estimated it
        # earlier and the frontend stored it back into the configuration.
        cor_offset = params.get("offset", 0.0)
        return preprocessing_ops.apply_cor_shift(data, cor_offset)

    # Ring/destriping operations
    elif short_name == "ring_filter":
        parameter = params.get("parameter", 0.1)
        if data.ndim == 2:
            # preprocessing_ops.ring_filter expects a stack; wrap a single
            # slice the same way apply_fov_mask does for tomopy, and unwrap
            # the result. Real stripe removal is more effective across a
            # full sinogram stack than one row -- see OPERATION_SCOPES.
            stacked = data[np.newaxis, :, :]
            return preprocessing_ops.ring_filter(stacked, parameter)[0]
        return preprocessing_ops.ring_filter(data, parameter)

    else:
        raise ValueError(f"Unknown operation: {short_name}")


def apply_operations_to_data(
    data: np.ndarray,
    configuration: PreprocessingConfiguration,
) -> np.ndarray:
    """
    Apply all enabled operations to data in order.

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


def cor_needs_estimation(parameters: dict) -> bool:
    """
    A COR operation needs broader-data estimation when the caller hasn't
    given it a concrete offset yet (or explicitly asked to auto-estimate).
    """
    return parameters.get("auto", False) or "offset" not in parameters


def estimate_cor_offset(dataset_service: Any, context: DataContext) -> float:
    """
    Estimate the center-of-rotation offset using the full sinogram stack.

    STILL INCOMPLETE: no COR estimation algorithm exists anywhere in this
    codebase yet (preprocessing_ops.py only has apply_cor_shift, which
    *applies* a known offset -- it doesn't find one). A real implementation
    would typically compare opposing projections (e.g. 0deg vs 180deg) or
    use something like TomoPy's find_center family of functions.

    Returns a neutral 0.0 offset for now so the pipeline doesn't break.
    Replace this function's body once a real estimator exists -- the call
    site (resolve_broad_scope_operation) doesn't need to change.
    """
    _ = dataset_service  # unused until a real estimator is implemented
    _ = context
    return 0.0


def resolve_broad_scope_operation(
    short_name: str,
    parameters: dict,
    dataset_service: Any,
    context: DataContext,
) -> dict:
    """
    Resolve an operation's broad-scope parameters into concrete,
    slice-applicable values. Returns a new dict -- never mutates the input.

    Called once (via POST /preprocessing/resolve), not per-frame and not on
    every preview request: the resolved value gets stored back into the
    frontend's configuration like any other parameter, so preview and
    full-stack apply both just see a plain number from then on.

    Only "cor" needs this today. Add new branches here as more operations
    grow a "stack"/"dataset" scope requirement (see OPERATION_SCOPES).
    """
    resolved = dict(parameters)

    if short_name == "cor" and cor_needs_estimation(resolved):
        resolved["offset"] = estimate_cor_offset(dataset_service, context)
        resolved["auto"] = True

    return resolved