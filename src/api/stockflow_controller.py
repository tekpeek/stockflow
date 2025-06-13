from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.responses import JSONResponse
import logging
import sys
import subprocess
import time
from typing import Dict, Any

# Configure logging to print to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

stockflow_controller = FastAPI()

def check_cronjob_exists() -> bool:
    try:
        result = subprocess.run(['kubectl', 'get', 'cronjob', 'signal-check-cronjob'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        return True
    except subprocess.CalledProcessError:
        logger.error("Cronjob signal-check-cronjob not found")
        return False

@stockflow_controller.get("/admin/trigger-cron")
async def trigger_cronjob() -> Dict[str, Any]:
    if not check_cronjob_exists():
        return JSONResponse(
            status_code=404,
            content={"status": "error", "detail": "signal-check-cronjob not found in the cluster"}
        )
    
    try:
        time_string = str(time.time())
        logger.info(f"Triggering manual cronjob on request at {time_string}")
        time_string = time_string.split('.')
        pod_suffix = time_string[0] + "-" + time_string[1]
        logger.info(f"Creating job from cronjob with suffix - {pod_suffix}")
        result = subprocess.run(
            ['kubectl', 'create', 'job', 'sf-cron-api-' + pod_suffix, '--from=cronjob/signal-check-cronjob'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Command Result: {result.stdout}")
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Cronjob triggered successfully",
                "job_name": f"sf-cron-api-{pod_suffix}",
                "details": result.stdout
            }
        )
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create job: {e.stderr}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": f"Failed to create job: {e.stderr}"}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": f"Unexpected error: {str(e)}"}
        )

if __name__ == "__main__":
    logger.info("Starting up stockflow controller server")
    uvicorn.run("stockflow_controller:stockflow_controller", host="0.0.0.0", port=9000, log_level="info")