from pydantic import BaseModel
from datetime import datetime


class WaterDataOut(BaseModel):
    box_id: str
    dissolved_oxygen: float
    temperature: float
    salinity: float
    timestamp: datetime
    health_index: float

    model_config = {"from_attributes": True}


class BoxListItem(BaseModel):
    box_id: str
