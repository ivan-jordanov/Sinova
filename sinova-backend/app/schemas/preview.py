from pydantic import BaseModel, Field

from .preprocessing import DataContext, PreprocessingConfiguration


class PreviewRequest(BaseModel):
    context: DataContext
    slice: int = Field(ge=0)
    configuration: PreprocessingConfiguration
    mode: str = "current"


class PreviewResponse(BaseModel):
    context: DataContext
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    data_format: str
    dtype: str
    data: list[float]
    request_id: str
    message: str