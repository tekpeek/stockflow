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
MAINTENANCE_STATUS = os.getenv("MAINTENANCE_STATUS")
market_intel = FastAPI()
client = AsyncOpenAI()

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
    time_stamp = datetime.datetime.now(datetime.UTC)
    if MAINTENANCE_STATUS == "on":
        logging.info("Skipping API call as service is in maintenance mode")
        return JSONResponse({"status": "Maintenance mode is enabled"})
    if not item.prompt:
        logging.info("Prompt is empty, skipping API call.")
        return JSONResponse({
            "result": "Prompt is empty",
            "timestamp": f"{time_stamp}"
        })
    try:
        completion = await client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": f"{item.prompt}",
            },
        ],
        )
    except Exception as e:
        logging.info(f"API call failed. Error: {e}")
        return JSONResponse({
            "result": "failed",
            "timestamp": f"{time_stamp}",
            "error": f"{e}"
        })
    time_stamp = datetime.datetime.now(datetime.UTC)
    final_result = completion.choices[0].message.content
    if not final_result:
        logging.info("Result is empty, printing model response.")
        print(completion)
        return JSONResponse({
            "result": "failed",
            "timestamp": f"{time_stamp}",
            "error": "Result is empty"
        })
    return JSONResponse({
            "result": f"{final_result}",
            "timestamp": f"{time_stamp}"
    })

if __name__ == "__main__":
    logger.info("Starting up market-intel-engine server")
    uvicorn.run("market_intel:market_intel", host="0.0.0.0", port=8000, log_level="info")