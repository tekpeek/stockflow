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
from pydantic import BaseModel

# Configure logging to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

class Item(BaseModel):
    prompt: str

# Get values from environment variables (Kubernetes ConfigMap/Secret)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

market_intel = FastAPI()

@market_intel.get("/health")
async def health_check():
    if MAINTENANCE_STATUS == "on":
        return JSONResponse({"status": "Maintenance mode is enabled"})
    time_stamp = datetime.datetime.now(datetime.UTC)
    return JSONResponse({
            "status": "OK",
            "timestamp": f"{time_stamp}"
    })

@market_intel.post("/chat")
async def push_prompt(item: Item):
    return item
    if MAINTENANCE_STATUS == "on":
        return JSONResponse({"status": "Maintenance mode is enabled"})
    logging.info("Triggering signal-engine for "+stock_id)
    logging.info(f"Strategy Values: interval: {interval}, period: {period}, window: {window}, num_std: {num_std}")

if __name__ == "__main__":
    logger.info("Starting up market-intel-engine server")
    uvicorn.run("market_intel:market_intel", host="0.0.0.0", port=8000, log_level="info")