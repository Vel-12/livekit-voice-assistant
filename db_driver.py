import os
import logging
from contextlib import contextmanager
from typing import Optional
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor

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
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable must be set for PostgreSQL.")
        logger.info(f"Initializing database at: {self.db_url}")
        self._init_db()

    @contextmanager
    def _get_connection(self):
        logger.info(f"Connecting to database at: {self.db_url}")
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
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
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (request_id, customer_name, email, phone_number, phone_type,
                     from_address, from_building_type, from_bedrooms, to_address,
                     move_date, flexible_date, assist_car, car_year, car_make, car_model)
                )
                conn.commit()
                logger.info(f"Successfully created moving request: {request_id}")
                
                # Verify the data was inserted
                cursor.execute("SELECT * FROM moving_requests WHERE request_id = %s", (request_id,))
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
            cursor.execute("SELECT * FROM moving_requests WHERE request_id = %s", (request_id,))
            row = cursor.fetchone()
            if not row:
                logger.info(f"No moving request found with ID: {request_id}")
                return None
            
            logger.info(f"Found moving request: {row}")
            return MovingRequest(
                request_id=row['request_id'],
                customer_name=row['customer_name'],
                email=row['email'],
                phone_number=row['phone_number'],
                phone_type=row['phone_type'],
                from_address=row['from_address'],
                from_building_type=row['from_building_type'],
                from_bedrooms=row['from_bedrooms'],
                to_address=row['to_address'],
                move_date=row['move_date'],
                flexible_date=row['flexible_date'],
                assist_car=row['assist_car'],
                car_year=row['car_year'],
                car_make=row['car_make'],
                car_model=row['car_model']
            )
