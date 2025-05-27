from livekit.agents import llm
import enum
from typing import Annotated, Optional
import logging
from db_driver import DatabaseDriver
import random

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()

def generate_request_id() -> str:
    """Generate a random 6-digit request ID."""
    return str(random.randint(100000, 999999))

class MovingDetails(enum.Enum):
    REQUEST_ID = "request_id"
    CUSTOMER_NAME = "customer_name"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    PHONE_TYPE = "phone_type"
    FROM_ADDRESS = "from_address"
    FROM_BUILDING_TYPE = "from_building_type"
    FROM_BEDROOMS = "from_bedrooms"
    TO_ADDRESS = "to_address"
    MOVE_DATE = "move_date"
    FLEXIBLE_DATE = "flexible_date"
    ASSIST_CAR = "assist_car"
    CAR_YEAR = "car_year"
    CAR_MAKE = "car_make"
    CAR_MODEL = "car_model"

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        self._current_request_id = generate_request_id()  # Only store the current request ID
    
    def get_current_request_id(self) -> str:
        """Get the current request ID."""
        return self._current_request_id
    
    def get_moving_request_str(self, request_id: str) -> str:
        """Format the moving request details in a clear, readable way."""
        result = DB.get_moving_request(request_id)
        if result is None:
            return "Moving request not found"
        
        # Format the output with exact spacing and formatting as specified in prompts
        request_str = "Here are your moving request details:\n"
        request_str += f"Request ID: {result.request_id}\n"
        request_str += f"Customer Name: {result.customer_name}\n"
        request_str += f"Email: {result.email}\n"
        request_str += f"Phone number: {result.phone_number}\n"
        request_str += f"From Address: {result.from_address}\n"
        request_str += f"Number of Bedrooms: {result.from_bedrooms}\n"
        request_str += f"To Address: {result.to_address}\n"
        request_str += f"Move Date: {result.move_date}\n"
        request_str += f"Flexible Date: {'Yes' if result.flexible_date else 'No'}\n"
        request_str += f"Car Transport: {'Yes' if result.assist_car else 'No'}\n"
        
        # Add a clear question with proper spacing
        request_str += "\nWould you like to make any changes to these details?"
        
        return request_str
    
    @llm.ai_callable(description="lookup a moving request by its ID")
    def lookup_moving_request(self, request_id: Annotated[str, llm.TypeInfo(description="The ID of the moving request to lookup")]):
        logger.info("lookup moving request - request_id: %s", request_id)
        return f"The moving request details are: {self.get_moving_request_str(request_id)}"
    
    @llm.ai_callable(description="get the details of the current moving request")
    def get_moving_request_details(self):
        logger.info("get moving request details")
        return f"The moving request details are: {self.get_moving_request_str(self._current_request_id)}"
    
    @llm.ai_callable(description="create a new moving request")
    def create_moving_request(
        self, 
        customer_name: Annotated[str, llm.TypeInfo(description="The name of the customer")],
        email: Annotated[str, llm.TypeInfo(description="The email of the customer")],
        phone_number: Annotated[str, llm.TypeInfo(description="The phone number of the customer")],
        phone_type: Annotated[str, llm.TypeInfo(description="The type of phone (cell, home, or work)")],
        from_address: Annotated[str, llm.TypeInfo(description="The address to move from")],
        from_building_type: Annotated[str, llm.TypeInfo(description="The type of building (house or apartment)")],
        from_bedrooms: Annotated[int, llm.TypeInfo(description="The number of bedrooms")],
        to_address: Annotated[str, llm.TypeInfo(description="The address to move to")],
        move_date: Annotated[str, llm.TypeInfo(description="The date of the move")],
        flexible_date: Annotated[bool, llm.TypeInfo(description="Whether the move date is flexible")],
        assist_car: Annotated[bool, llm.TypeInfo(description="Whether car transportation is needed")],
        car_year: Annotated[Optional[str], llm.TypeInfo(description="The year of the car (if car transportation is needed)")] = None,
        car_make: Annotated[Optional[str], llm.TypeInfo(description="The make of the car (if car transportation is needed)")] = None,
        car_model: Annotated[Optional[str], llm.TypeInfo(description="The model of the car (if car transportation is needed)")] = None
    ):
        request_id = self._current_request_id
        logger.info("create moving request - request_id: %s", request_id)
        
        result = DB.create_moving_request(
            request_id, customer_name, email, phone_number, phone_type,
            from_address, from_building_type, from_bedrooms, to_address,
            move_date, flexible_date, assist_car, car_year, car_make, car_model
        )
        if result is None:
            return "Failed to create moving request"
        
        return f"Moving request created! Your request ID is: {request_id}. Please save this ID for future reference."
    
    def has_moving_request(self) -> bool:
        """Check if we have a complete moving request in the database."""
        result = DB.get_moving_request(self._current_request_id)
        if result is None:
            return False
            
        required_fields = [
            result.customer_name,
            result.email,
            result.phone_number,
            result.phone_type,
            result.from_address,
            result.from_building_type,
            result.from_bedrooms,
            result.to_address,
            result.move_date,
            result.flexible_date,
            result.assist_car
        ]
        return all(field for field in required_fields)

    @llm.ai_callable(description="get additional details for a moving request")
    def get_additional_details(self, request_id: Annotated[str, llm.TypeInfo(description="The ID of the moving request")], 
                             field: Annotated[str, llm.TypeInfo(description="The field to get details for (phone_type, building_type, car_details)")]):
        """Get additional details for specific fields when requested."""
        result = DB.get_moving_request(request_id)
        if result is None:
            return "Moving request not found"
        
        if field.lower() == "phone_type":
            return f"Phone type: {result.phone_type}"
        elif field.lower() == "building_type":
            return f"Building Type: {result.from_building_type}"
        elif field.lower() == "car_details" and result.assist_car:
            return f"Car Year: {result.car_year}\nCar Make: {result.car_make}\nCar Model: {result.car_model}"
        elif field.lower() == "car_details" and not result.assist_car:
            return "Car transport is not needed for this request."
        else:
            return f"Field '{field}' not found or not available."