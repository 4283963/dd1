from sqlalchemy import Column, String, Float, DateTime, Index
from .database import Base


class SeaWaterData(Base):
    __tablename__ = "sea_water_data"

    id = Column(String, primary_key=True)
    box_id = Column(String, nullable=False, index=True)
    dissolved_oxygen = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    salinity = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("ix_box_timestamp", "box_id", "timestamp"),
    )
