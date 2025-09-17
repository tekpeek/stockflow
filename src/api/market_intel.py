from fastapi import FastAPI
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import datetime
import logging
import sys
import os
import numpy as np
from openai import AsyncOpenAI
import asyncio

# Configure logging to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Get values from environment variables (Kubernetes ConfigMap/Secret)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def convert_bools_to_strings(data):
    if isinstance(data, dict):
        return {k: convert_bools_to_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_bools_to_strings(item) for item in data]
    elif isinstance(data, (bool, np.bool_)):  # Handle both Python bool and NumPy bool
        return str(data)
    return data

market_intel = FastAPI()

@signal_engine.get("/health")
def health_check():
    if MAINTENANCE_STATUS == "on":
        return JSONResponse({"status": "Maintenance mode is enabled"})
    time_stamp = datetime.datetime.now(datetime.UTC)
    return JSONResponse({
            "status": "OK",
            "timestamp": f"{time_stamp}"
    })

@signal_engine.get("/chat")
def get_stock_data(
    stock_id: str,
    interval: str = DEFAULT_INTERVAL,
    period: int = DEFAULT_PERIOD,
    window: int = DEFAULT_WINDOW,
    num_std: float = DEFAULT_NUM_STD
):
    if MAINTENANCE_STATUS == "on":
        return JSONResponse({"status": "Maintenance mode is enabled"})
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
    logger.info("Starting up market-intel-engine server")
    uvicorn.run("market_intel:market_intel", host="0.0.0.0", port=8000, log_level="info")