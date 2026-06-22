import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, SeaWaterData

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/seawater"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    box_ids = [f"BOX-{i:03d}" for i in range(1, 7)]
    now = datetime.utcnow()

    records = []
    for box_id in box_ids:
        for i in range(96):
            ts = now - timedelta(minutes=15 * (95 - i))
            do_val = random.gauss(7.5, 1.2)
            do_val = max(2.0, min(14.0, do_val))
            if box_id == "BOX-003":
                do_val = random.gauss(4.2, 0.8)
            temp_val = random.gauss(22.0, 3.0)
            temp_val = max(10.0, min(35.0, temp_val))
            if box_id == "BOX-005":
                temp_val = random.gauss(30.0, 1.5)
            sal_val = random.gauss(31.0, 2.0)
            sal_val = max(20.0, min(42.0, sal_val))
            records.append(
                SeaWaterData(
                    id=str(uuid.uuid4()),
                    box_id=box_id,
                    dissolved_oxygen=round(do_val, 2),
                    temperature=round(temp_val, 2),
                    salinity=round(sal_val, 2),
                    timestamp=ts,
                )
            )

    db.bulk_save_objects(records)
    db.commit()
    db.close()
    print(f"Seeded {len(records)} records for boxes: {box_ids}")


if __name__ == "__main__":
    seed()
