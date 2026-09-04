from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.core.config import OPERATION_DEPENDENCIES

DataContext = Literal["projection", "sinogram"]


class Operation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    short_name: str = Field(
        min_length=1,
        validation_alias=AliasChoices("short_name", "shortName"),
    )
    category: Literal["intensity", "spatial", "geometry", "destriping"]
    description: str = ""
    enabled: bool
    scope: Literal["slice", "stack", "dataset"]
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires: list[str] = Field(default_factory=list)


class OperationInfo(BaseModel):
    """Operation metadata for frontend constraint display."""

    id: str
    name: str
    short_name: str
    category: Literal["intensity", "spatial", "geometry", "destriping"]
    description: str
    requires: list[str]


class PreprocessingConfiguration(BaseModel):
    operations: list[Operation]

    def validate_operation_order(self) -> None:
        """Validate that operations are in correct dependency order.

        Raises:
            ValueError: If an operation requires another that isn't enabled first
        """
        enabled_ops = {op.short_name for op in self.operations if op.enabled}

        for op in self.operations:
            if not op.enabled:
                continue

            # Check all dependencies
            deps = OPERATION_DEPENDENCIES.get(op.short_name, [])
            for dep in deps:
                if dep not in enabled_ops:
                    raise ValueError(
                        f"Operation '{op.name}' requires '{dep}' to be enabled"
                    )

            # Check that dep comes before this op
            dep_indices = {
                i
                for i, o in enumerate(self.operations)
                if o.short_name in deps and o.enabled
            }
            op_index = next(
                i for i, o in enumerate(self.operations) if o.short_name == op.short_name
            )
            if dep_indices and max(dep_indices) >= op_index:
                dep_name = next(
                    o.name
                    for o in self.operations
                    if o.short_name in deps
                    and o.enabled
                    and self.operations.index(o) >= op_index
                )
                raise ValueError(
                    f"Operation '{op.name}' must come after '{dep_name}'"
                )


class ApplyPreprocessingRequest(BaseModel):
    configuration: PreprocessingConfiguration


class ProcessingStatus(BaseModel):
    status: Literal["idle", "queued", "processing", "completed", "failed"]
    job_id: str | None = None
    message: str