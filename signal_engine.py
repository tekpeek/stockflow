from fastapi import FastAPI
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import signal_functions as sf
import logging
import sys
import os

# Configure logging to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
interval = os.getenv("INTERVAL")
period = os.getenv("PERIOD")
window = os.getenv("WINDOW")
num_std = os.getenv("NUM_STD")
signal_engine = FastAPI()

@signal_engine.get("/{stock_id}")
def get_stock_data(stock_id: str,interval: str,period: int,window: int, num_std: float):
    logging.info("Triggering signal-engine for "+stock_id)
    logging.info(f"Strategy Values: interval: {interval}, period: {period}, window: {window}, num_std: {num_std}")
    if stock_id.endswith(".NS"):
        try:
            return_data = sf.calculate_final_signal(stock_id,interval,period,window,num_std)
            if return_data is None:
                logger.error("Return data is None")
                return JSONResponse({"error": "No data returned from signal calculation"})
            return JSONResponse(return_data)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JSONResponse({"error": f"Failed to process stock data: {str(e)}"})
    else:
        logger.warning(f"Invalid format: {stock_id}")
        return JSONResponse({"error": "Incorrect Stock ID. Stock ID must end with .NS"})

if __name__ == "__main__":
    logger.info("Starting up signal-engine server")
    uvicorn.run("signal_engine:signal_engine", host="0.0.0.0", port=8000, log_level="info")