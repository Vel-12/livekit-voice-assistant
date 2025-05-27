import sqlite3
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MovingRequest:
    request_id: str
    customer_name: str
    email: str
    phone_number: str
    phone_type: str  # cell, home, or work
    from_address: str
    from_building_type: str  # house or apartment
    from_bedrooms: int
    to_address: str
    move_date: str
    flexible_date: bool
    assist_car: bool
    car_year: Optional[str]
    car_make: Optional[str]
    car_model: Optional[str]

class DatabaseDriver:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get the directory where this file is located
            # current_dir = os.path.dirname(os.path.abspath(__file__))
            # self.db_path = os.path.join(current_dir, "moving_db.sqlite")
            self.db_path = "/app/data/moving_db.sqlite"
        else:
            self.db_path = db_path
        logger.info(f"Initializing database at: {self.db_path}")
        self._init_db()

    @contextmanager
    def _get_connection(self):
        logger.info(f"Connecting to database at: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
            logger.info("Database connection closed")

    def _init_db(self):
        logger.info("Initializing database schema...")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create moving_requests table with all required fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS moving_requests (
                    request_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    phone_type TEXT NOT NULL,
                    from_address TEXT NOT NULL,
                    from_building_type TEXT NOT NULL,
                    from_bedrooms INTEGER NOT NULL,
                    to_address TEXT NOT NULL,
                    move_date TEXT NOT NULL,
                    flexible_date BOOLEAN NOT NULL,
                    assist_car BOOLEAN NOT NULL,
                    car_year TEXT,
                    car_make TEXT,
                    car_model TEXT
                )
            """)
            conn.commit()
            logger.info("Database schema initialized successfully")

    def create_moving_request(
        self, 
        request_id: str,
        customer_name: str,
        email: str,
        phone_number: str,
        phone_type: str,
        from_address: str,
        from_building_type: str,
        from_bedrooms: int,
        to_address: str,
        move_date: str,
        flexible_date: bool,
        assist_car: bool,
        car_year: Optional[str] = None,
        car_make: Optional[str] = None,
        car_model: Optional[str] = None
    ) -> MovingRequest:
        logger.info(f"Creating moving request with ID: {request_id}")
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                # Log the data being inserted
                logger.info(f"Inserting data: request_id={request_id}, customer_name={customer_name}, email={email}")
                
                cursor.execute(
                    """INSERT INTO moving_requests 
                       (request_id, customer_name, email, phone_number, phone_type,
                        from_address, from_building_type, from_bedrooms, to_address,
                        move_date, flexible_date, assist_car, car_year, car_make, car_model) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (request_id, customer_name, email, phone_number, phone_type,
                     from_address, from_building_type, from_bedrooms, to_address,
                     move_date, flexible_date, assist_car, car_year, car_make, car_model)
                )
                conn.commit()
                logger.info(f"Successfully created moving request: {request_id}")
                
                # Verify the data was inserted
                cursor.execute("SELECT * FROM moving_requests WHERE request_id = ?", (request_id,))
                row = cursor.fetchone()
                if row:
                    logger.info(f"Verified data insertion: {row}")
                else:
                    logger.error("Data insertion verification failed - no row found")
                
                return MovingRequest(
                    request_id=request_id,
                    customer_name=customer_name,
                    email=email,
                    phone_number=phone_number,
                    phone_type=phone_type,
                    from_address=from_address,
                    from_building_type=from_building_type,
                    from_bedrooms=from_bedrooms,
                    to_address=to_address,
                    move_date=move_date,
                    flexible_date=flexible_date,
                    assist_car=assist_car,
                    car_year=car_year,
                    car_make=car_make,
                    car_model=car_model
                )
            except Exception as e:
                logger.error(f"Error creating moving request: {str(e)}")
                raise

    def get_moving_request(self, request_id: str) -> Optional[MovingRequest]:
        logger.info(f"Looking up moving request with ID: {request_id}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM moving_requests WHERE request_id = ?", (request_id,))
            row = cursor.fetchone()
            if not row:
                logger.info(f"No moving request found with ID: {request_id}")
                return None
            
            logger.info(f"Found moving request: {row}")
            return MovingRequest(
                request_id=row[0],
                customer_name=row[1],
                email=row[2],
                phone_number=row[3],
                phone_type=row[4],
                from_address=row[5],
                from_building_type=row[6],
                from_bedrooms=row[7],
                to_address=row[8],
                move_date=row[9],
                flexible_date=bool(row[10]),
                assist_car=bool(row[11]),
                car_year=row[12],
                car_make=row[13],
                car_model=row[14]
            )
