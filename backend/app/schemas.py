from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WaterDataOut(BaseModel):
    box_id: str
    dissolved_oxygen: Optional[float] = None
    temperature: Optional[float] = None
    salinity: Optional[float] = None
    timestamp: datetime
    health_index: Optional[float] = None
    missing_fields: list[str] = []

    model_config = {"from_attributes": True}


class BoxListItem(BaseModel):
    box_id: str
