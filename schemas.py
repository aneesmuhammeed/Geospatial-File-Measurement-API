from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class FileResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: str
    status: str

    class Config:
        from_attributes = True

class FeatureMeasurementResponse(BaseModel):
    feature_index: int
    geometry_type: str
    area: Optional[float] = None
    length: Optional[float] = None

    class Config:
        from_attributes = True

class MeasurementListResponse(BaseModel):
    id: str
    measurements: List[FeatureMeasurementResponse]
