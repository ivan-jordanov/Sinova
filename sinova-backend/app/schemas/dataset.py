from pydantic import BaseModel, Field

class BrowseResponse(BaseModel):
    path: str


class LoadDatasetRequest(BaseModel):
    path: str

class DatasetMetadata(BaseModel):
    name: str
    detector_width: int = Field(gt=0)
    detector_height: int = Field(gt=0)
    projections: int = Field(gt=0)
    format: str


class LoadDatasetRequest(BaseModel):
    path: str = Field(min_length=1)


class LoadDatasetResponse(BaseModel):
    loaded: bool
    metadata: DatasetMetadata
    
    