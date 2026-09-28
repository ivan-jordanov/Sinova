"""Domain constants for preprocessing operations."""

OPERATION_DEPENDENCIES: dict[str, list[str]] = {
    "normalize": [],
    "negative_log": ["normalize"],
    "clip_attenuation": [],
    "fov_mask": [],
    "crop_pad_beam": [],
    "mutate": [],
    "denoise": [],
    "cor_shift": [],
    "ring_filter_fw": [],
    "ring_filter_vo": [],
    "ring_filter_inr": [],
}

OPERATION_SCOPES: dict[str, str] = {
    "normalize": "both",
    "negative_log": "both",
    "clip_attenuation": "both",
    "fov_mask": "projection",
    "crop_pad_beam": "projection",
    "mutate": "sinogram",
    "denoise": "both",
    "cor_shift": "sinogram",
    "ring_filter_fw": "sinogram",
    "ring_filter_vo": "sinogram",
    "ring_filter_inr": "sinogram",
}

GPU_BOUND_OPERATIONS = {"ring_filter_inr"}
BROAD_SCOPE_OPERATIONS = {"mutate", "cor_shift"}