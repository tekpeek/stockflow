from fastapi import FastAPI
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import signal_functions as sf
import logging
import sys
import os
import numpy as np
import datetime
from backtest_functions import calculate_bulk_backtest, calculate_bulk_backtest_overall, backtest_prediction_accuracy, backtest_prediction_single_accuracy
# Configure logging to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Get values from environment variables (Kubernetes ConfigMap/Secret)
DEFAULT_INTERVAL = os.getenv("INTERVAL")
DEFAULT_PERIOD = int(os.getenv("PERIOD"))
DEFAULT_WINDOW = int(os.getenv("WINDOW"))
DEFAULT_NUM_STD = float(os.getenv("NUM_STD"))

def convert_bools_to_strings(data):
    if isinstance(data, dict):
        return {k: convert_bools_to_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_bools_to_strings(item) for item in data]
    elif isinstance(data, (bool, np.bool_)):  # Handle both Python bool and NumPy bool
        return str(data)
    return data

signal_engine = FastAPI()

@signal_engine.get("/health")
def health_check():
    time_stamp = datetime.datetime.now(datetime.UTC)
    return JSONResponse({
            "status": "OK",
            "timestamp": f"{time_stamp}"
    })

@signal_engine.get("/backtest")
def backtest():
    logging.info("Backtesting for all")
    if True:
        try:
            return_data = calculate_bulk_backtest_overall()
            if return_data is None:
                logger.error("Return data is None")
                return JSONResponse({"error": "No data returned from signal calculation"})
            return JSONResponse(return_data)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JSONResponse({"error": f"Failed to process stock data: {str(e)}"})
    else:
        logger.warning(f"Invalid format: {option}")
        return JSONResponse({"error": "Incorrect Stock ID. Stock ID must end with .NS"})

@signal_engine.get("/backtest/ind/{option}")
def backtest(
    option: str,
):
    logging.info("Backtesting for "+option)
    if option in ["rsi","macd","bb","cmf"]:
        try:
            return_data = calculate_bulk_backtest(option)
            if return_data is None:
                logger.error("Return data is None")
                return JSONResponse({"error": "No data returned from signal calculation"})
            return JSONResponse(return_data)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JSONResponse({"error": f"Failed to process stock data: {str(e)}"})
    else:
        logger.warning(f"Invalid format: {option}")
        return JSONResponse({"error": "Incorrect Stock ID. Stock ID must end with .NS"})

@signal_engine.get("/backtest/{stock_id}")
def backtest(
    stock_id: str,
    interval: str = DEFAULT_INTERVAL,
    period: int = DEFAULT_PERIOD,
    window: int = DEFAULT_WINDOW,
    num_std: float = DEFAULT_NUM_STD
):
    logging.info("Triggering signal-engine for "+stock_id)
    logging.info(f"Strategy Values: interval: {interval}, period: {period}, window: {window}, num_std: {num_std}")
    if stock_id.endswith(".NS"):
        try:
            return_data = backtest_prediction_accuracy(stock_id,interval,period,window,num_std)
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
    
@signal_engine.get("/backtest/{stock_id}/{option}")
def backtest(
    stock_id: str,
    option: str,
    interval: str = DEFAULT_INTERVAL,
    period: int = DEFAULT_PERIOD,
    window: int = DEFAULT_WINDOW,
    num_std: float = DEFAULT_NUM_STD
):
    logging.info("Triggering signal-engine for "+stock_id)
    logging.info(f"Strategy Values: interval: {interval}, period: {period}, window: {window}, num_std: {num_std}")
    if stock_id.endswith(".NS"):
        try:
            return_data = backtest_prediction_single_accuracy(option,stock_id,interval,period,window,num_std)
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

@signal_engine.get("/{stock_id}")
def get_stock_data(
    stock_id: str,
    interval: str = DEFAULT_INTERVAL,
    period: int = DEFAULT_PERIOD,
    window: int = DEFAULT_WINDOW,
    num_std: float = DEFAULT_NUM_STD
):
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
    
@signal_engine.get("/{stock_id}/{option}")
def get_stock_data(
    stock_id: str,
    option: str = 'rsi',
    interval: str = DEFAULT_INTERVAL,
    period: int = DEFAULT_PERIOD,
    window: int = DEFAULT_WINDOW,
    num_std: float = DEFAULT_NUM_STD
):
    logging.info("Triggering signal-engine for "+stock_id)
    logging.info(f"Strategy Values: interval: {interval}, period: {period}, window: {window}, num_std: {num_std}")
    if stock_id.endswith(".NS"):
        try:
            return_data = sf.calculate_individual(option,stock_id,interval,period,window,num_std)
            return_data = convert_bools_to_strings(return_data)
            print(return_data)
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
    uvicorn.run("signal_engine:signal_engine", host="0.0.0.0", port=8001, log_level="info",reload=True)