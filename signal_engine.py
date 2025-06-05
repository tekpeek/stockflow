from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import signal_functions as sf
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

signal_engine = FastAPI()

@signal_engine.get("/{stock_id}")
def get_stock_data(stock_id: str):
    print("Stock ID: "+stock_id)
    if stock_id.endswith(".NS"):
        try:
            return JSONResponse({"error": "No data returned from signal calculation"})
            return_data = sf.calculate_final_signal(stock_id)
            """print("Return data:", return_data)  # Debug print
            if return_data is None:
                logger.error("Return data is None")
                return JSONResponse({"error": "No data returned from signal calculation"})
            return JSONResponse(return_data)"""
            return JSONResponse({"error": "No data returned from signal calculation"})
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JSONResponse({"error": f"Failed to process stock data: {str(e)}"})
    else:
        logger.warning(f"Invalid format: {stock_id}")
        return JSONResponse({"error": "Incorrect Stock ID. Stock ID must end with .NS"})