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
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
DEPLOY_TYPE = os.getenv("DEPLOY_TYPE")

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.BatchV1Api()
v1_core = client.CoreV1Api()
v1_core_apps = client.AppsV1Api()
stockflow_controller = FastAPI()

if DEPLOY_TYPE != "default":
    DEPLOY_TYPE = "/"+DEPLOY_TYPE
else:
    DEPLOY_TYPE = "/"

router = APIRouter()

# Add CORS middleware
stockflow_controller.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

@router.get("/api/admin/health")
def health_check():
    time_stamp = datetime.datetime.now(datetime.UTC)
    return JSONResponse({
            "status": "OK",
            "timestamp": f"{time_stamp}"
    })

@router.get("/api/admin/maintenance/status")
async def get_maintenance_status():
    time_stamp = datetime.datetime.now(datetime.UTC)
    configmap = v1_core.read_namespaced_config_map(name="maintenance-config",namespace="default")
    existing_status = configmap.data['status']
    return JSONResponse({
        "status": existing_status,
        "timestamp": f"{time_stamp}"
    })

@router.get("/api/admin/maintenance/{status}")
async def enable_maintenance(status: str, dep=Depends(api_key_auth)) -> Dict[str, Any]:
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
    
    configmap = v1_core.read_namespaced_config_map(name="maintenance-config",namespace="default")
    existing_status = configmap.data['status']
    print("Status : ",existing_status)
    if existing_status != status:
        configmap.data['status'] = status
        response = v1_core.patch_namespaced_config_map(name="maintenance-config",namespace="default",body=configmap)
        print("Response : ",response)
        # Perform a rollout restart by updating an annotation
        deployment = v1_core_apps.read_namespaced_deployment(name="signal-engine", namespace="default")
        if not deployment.spec.template.metadata.annotations:
            deployment.spec.template.metadata.annotations = {}
        import time as _time
        deployment.spec.template.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = datetime.datetime.utcnow().isoformat()
        response = v1_core_apps.patch_namespaced_deployment(name="signal-engine", namespace="default", body=deployment)
        print("Rollout restart response : ", response)
        return JSONResponse({
                "status": f"{status}",
                "timestamp": f"{time_stamp}"
        })
    return JSONResponse({
            "status": f"{status}",
            "timestamp": f"{time_stamp}"
        })
    

@router.get("/api/admin/trigger-cron")
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
stockflow_controller.include_router(router,prefix=DEPLOY_TYPE)
if __name__ == "__main__":
    logger.info("Starting up stockflow controller server")
    uvicorn.run("stockflow_controller:stockflow_controller", host="0.0.0.0", port=9000, log_level="info")
