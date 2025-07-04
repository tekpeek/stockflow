from fastapi import FastAPI, HTTPException, Depends, Request
import uvicorn
from fastapi.responses import JSONResponse
import logging
import sys
import time
import datetime
from typing import Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.BatchV1Api()
stockflow_controller = FastAPI()

def api_key_auth(request: Request):
    api_key = request.headers.get('X-API-Key')
    expected_key = os.getenv('SF_API_KEY')
    if not api_key or api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

def check_cronjob_exists() -> bool:
    try:
        v1.read_namespaced_cron_job(
            name="signal-check-cronjob",
            namespace="default"
        )
        return True
    except ApiException as e:
        logger.error(f"Cronjob not found: {str(e)}")
        return False

@stockflow_controller.get("/api/admin/health")
def health_check():
    time_stamp = datetime.datetime.now(datetime.UTC)
    return JSONResponse({
            "status": "OK",
            "timestamp": f"{time_stamp}"
    })

@stockflow_controller.get("/api/admin/maintenance/{status}")
def enable_maintenance(status: str):
    time_stamp = datetime.datetime.now(datetime.UTC)
    if status == "on":
        result = "Maintenance mode enabled"
    elif status == "off":
        result = "Maintenance mode disabled"
    else:
        result = "Invalid status"
        return JSONResponse({
            "status": f"{status}",
            "timestamp": f"{time_stamp}"
        })
    return JSONResponse({
            "status": f"{result}",
            "timestamp": f"{time_stamp}"
    })

@stockflow_controller.get("/api/admin/trigger-cron")
async def trigger_cronjob(dep=Depends(api_key_auth)) -> Dict[str, Any]:
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
        job_name = f"sf-cron-api-{pod_suffix}"
        
        cronjob = v1.read_namespaced_cron_job(
            name="signal-check-cronjob",
            namespace="default"
        )
        
        job = client.V1Job(
            metadata=client.V1ObjectMeta(
                name=job_name,
                owner_references=[{
                    "apiVersion": "batch/v1",
                    "kind": "CronJob",
                    "name": "signal-check-cronjob",
                    "uid": cronjob.metadata.uid
                }]
            ),
            spec=cronjob.spec.job_template.spec
        )
        
        created_job = v1.create_namespaced_job(
            namespace="default",
            body=job
        )
        
        logger.info(f"Job created successfully from cronjob: {job_name}")
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Job created successfully from cronjob",
                "job_name": job_name,
                "details": f"Job {job_name} created in namespace default"
            }
        )
        
    except ApiException as e:
        logger.error(f"Failed to create job: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": f"Failed to create job: {str(e)}"}
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