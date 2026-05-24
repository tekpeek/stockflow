from fastapi import FastAPI
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import datetime
import logging
import sys
import os
from openai import AsyncOpenAI
import asyncio
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

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

class Element(BaseModel):
    symbol: str = Field(description="The ticker symbol of the stock, capitalized (e.g., RELIANCE.NS).")
    buy_rating: int = Field(description="0-7 (Integer - Your final confidence score). Assign buy_rating based on total confluence: - 0-2: Avoid/Invalidated - 3-4: Wait for trigger - 5-7: High-probability entry (Institutional/Professional grade)")
    overall_sentiment: str = Field(description="positive/neutral/negative")
    key_drivers: List[str] = Field(description="List of key factors driving the current sentiment and outlook.")
    confidence: int = Field(description="0-100. Your confidence in the analysis and prediction.")
    summary: str = Field(description="### Structure Summary: [Context]. ### Thesis: [Scenario & Triggers]. ### Forecast: P(up)=[X]%, P(down)=[Y]%, for 2-7 days.")

class ModelOutput(BaseModel):
    status: str = Field(description="success/failed. In case of failure to analyze, set 'status' to 'failed' and return an empty list for 'results'.")
    results: List[Element] = Field(description="List of analyzed stocks. Empty if status is 'failed'.")

class ModelOutputWrapper(BaseModel):
    mie_analysis: ModelOutput

# Get values from environment variables (Kubernetes ConfigMap/Secret)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAINTENANCE_STATUS = os.getenv("MAINTENANCE_STATUS")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

market_intel = FastAPI()
client = AsyncOpenAI()
gemini_client = None

if LLM_PROVIDER == "gemini":
    logger.info("Using Gemini LLM provider")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

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
        if LLM_PROVIDER == "gemini":
            response = await gemini_client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=item.prompt,
                config=types.GenerateContentConfig(
                    response_mime_type= 'application/json',
                    response_schema=ModelOutputWrapper.model_json_schema()
                )
            )
            final_result = response.text
            full_response_obj = response
        else:
            completion = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "user",
                    "content": f"{item.prompt}",
                },
            ],
            response_format={"type": "json_object"}
            )
            final_result = completion.choices[0].message.content
            full_response_obj = completion
    except Exception as e:
        logging.info(f"API call failed. Error: {e}")
        return JSONResponse({
            "result": "failed",
            "timestamp": f"{time_stamp}",
            "error": f"{e}"
        })
    time_stamp = datetime.datetime.now(datetime.UTC)
    if not final_result:
        logging.info("Result is empty, printing model response.")
        print(full_response_obj)
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