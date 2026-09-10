from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.core.config import OPERATION_DEPENDENCIES, OPERATION_SCOPES

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
    # Scope is a property of the operation *type*, not something the caller
    # should have to supply -- the frontend doesn't send it today, so it's
    # filled in from OPERATION_SCOPES if omitted.
    scope: Literal["slice", "stack", "dataset"] | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _default_scope_from_registry(self) -> "Operation":
        if self.scope is None:
            self.scope = OPERATION_SCOPES.get(self.short_name, "slice")
        return self


class OperationInfo(BaseModel):
    """Operation metadata for frontend constraint display."""

    id: str
    name: str
    short_name: str
    category: Literal["intensity", "spatial", "geometry", "destriping"]
    description: str
    requires: list[str]
    scope: Literal["slice", "stack", "dataset"] = "slice"


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

            deps = OPERATION_DEPENDENCIES.get(op.short_name, [])
            for dep in deps:
                if dep not in enabled_ops:
                    raise ValueError(
                        f"Operation '{op.name}' requires '{dep}' to be enabled"
                    )

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


class JobStatus(BaseModel):
    """Response for job status queries."""

    id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress: int = Field(ge=0, le=100)
    message: str = ""
    current_operation: str | None = None
    error: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None


class ProcessingStatus(BaseModel):
    """Deprecated: Use JobStatus instead. Kept for compatibility."""

    status: Literal["idle", "queued", "processing", "completed", "failed"]
    job_id: str | None = None
    message: str


class ResolveOperationRequest(BaseModel):
    """
    Request to resolve an operation's broad-scope parameters (e.g. COR
    estimation) into concrete values.

    The frontend calls this once (e.g. when the user enables/toggles
    auto-estimate on an operation), merges the returned parameters back
    into its own configuration state, and from then on preview/apply just
    use that configuration unchanged -- no scope logic needed there.
    """

    short_name: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    context: DataContext


class ResolveOperationResponse(BaseModel):
    parameters: dict[str, Any]