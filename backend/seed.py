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

            do_out = round(do_val, 2)
            temp_out = round(temp_val, 2)
            sal_out = round(sal_val, 2)

            if box_id in ("BOX-002", "BOX-006") and random.random() < 0.15:
                which = random.choice(["do", "temp", "sal", "do_temp"])
                if which == "do":
                    do_out = None
                elif which == "temp":
                    temp_out = None
                elif which == "sal":
                    sal_out = None
                else:
                    do_out = None
                    temp_out = None
            if box_id == "BOX-004" and random.random() < 0.4:
                which = random.choice(["do", "temp", "sal"])
                if which == "do":
                    do_out = None
                elif which == "temp":
                    temp_out = None
                else:
                    sal_out = None

            records.append(
                SeaWaterData(
                    id=str(uuid.uuid4()),
                    box_id=box_id,
                    dissolved_oxygen=do_out,
                    temperature=temp_out,
                    salinity=sal_out,
                    timestamp=ts,
                )
            )

    db.bulk_save_objects(records)
    db.commit()
    db.close()
    print(f"Seeded {len(records)} records for boxes: {box_ids}")
    print("  BOX-002/BOX-006: ~15% 数据存在指标缺失")
    print("  BOX-004: ~40% 数据存在指标缺失（模拟新投产硬件不稳定）")
    print("  BOX-003: 溶解氧偏低（预警）")
    print("  BOX-005: 温度偏高（预警）")


if __name__ == "__main__":
    seed()
