from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from .database import get_db
from .models import SeaWaterData
from .schemas import WaterDataOut, BoxListItem
from .health_index import calc_health_index

router = APIRouter(prefix="/api", tags=["water"])


@router.get("/boxes", response_model=list[BoxListItem])
def list_boxes(db: Session = Depends(get_db)):
    rows = db.query(distinct(SeaWaterData.box_id)).order_by(SeaWaterData.box_id).all()
    return [BoxListItem(box_id=r[0]) for r in rows]


@router.get("/water/{box_id}", response_model=list[WaterDataOut])
def get_water_data(box_id: str, db: Session = Depends(get_db)):
    try:
        since = datetime.utcnow() - timedelta(hours=24)
        rows = (
            db.query(SeaWaterData)
            .filter(SeaWaterData.box_id == box_id, SeaWaterData.timestamp >= since)
            .order_by(SeaWaterData.timestamp.asc())
            .all()
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"网箱 {box_id} 最近24小时无数据")
        result = []
        for r in rows:
            try:
                health_idx, missing = calc_health_index(
                    r.dissolved_oxygen, r.temperature, r.salinity
                )
            except Exception:
                health_idx, missing = None, ["calc_error"]
            try:
                result.append(
                    WaterDataOut(
                        box_id=r.box_id,
                        dissolved_oxygen=r.dissolved_oxygen,
                        temperature=r.temperature,
                        salinity=r.salinity,
                        timestamp=r.timestamp,
                        health_index=health_idx,
                        missing_fields=missing,
                    )
                )
            except Exception:
                continue
        if not result:
            raise HTTPException(status_code=404, detail=f"网箱 {box_id} 数据全部异常")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
