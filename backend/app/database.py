import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from backend.app.config import settings, logger
from backend.app.models.sql_models import Base, ConsumptionRecord
from backend.app.data.generator import save_synthetic_dataset

DATABASE_URL = settings.DATABASE_URL

# Create database engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency yielding database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database tables. If the database is empty, automatically generates
    realistic synthetic historical records and populates tables.
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    
    # Check if we already have records
    db = SessionLocal()
    try:
        count = db.query(ConsumptionRecord).count()
        if count == 0:
            logger.info("Database is empty. Populating with initial synthetic historical data...")
            
            # Generate dataset
            csv_path = save_synthetic_dataset(num_days=500)
            
            # Load into database
            df = pd.read_csv(csv_path)
            
            records_to_insert = []
            for _, row in df.iterrows():
                record = ConsumptionRecord(
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    day_of_week=row["day_of_week"],
                    temperature=float(row["temperature"]),
                    weather=row["weather"],
                    is_holiday=int(row["is_holiday"]),
                    event=row["event"],
                    visitors=int(row["visitors"]),
                    cooked_quantity=int(row["cooked_quantity"]),
                    actual_consumption=int(row["actual_consumption"]),
                    waste_generated=float(row["waste_generated"])
                )
                records_to_insert.append(record)
                
            db.bulk_save_objects(records_to_insert)
            db.commit()
            logger.info(f"Database successfully initialized with {len(records_to_insert)} historical consumption records.")
        else:
            logger.info(f"Database contains existing data ({count} records). Skipping synthetic ingestion.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing database: {e}")
    finally:
        db.close()
