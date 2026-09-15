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
from app.services.business.dataset_access import get_dataset_service

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
        return preprocessing_ops.clip_attenuation(data, max_value=max_value), operation

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

    elif short_name == "edge_enhance":
        raise NotImplementedError(
            "Edge Enhance has no implementation yet in preprocessing_ops.py"
        )

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

    return resolved