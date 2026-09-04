from pydantic import BaseModel, Field

from .preprocessing import PreprocessingConfiguration


class ExportRequest(BaseModel):
    configuration: PreprocessingConfiguration
    format: str = Field(default="mraw", min_length=1)


class ExportResponse(BaseModel):
    accepted: bool
    job_id: str
    message: str