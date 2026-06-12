import os
import httpx
import logging

logger = logging.getLogger(__name__)

class OrthancClient:
    def __init__(self):
        self.url = os.getenv("ORTHANC_URL", "http://localhost:8042")
        # Default Orthanc credentials if not specified in production
        self.auth = (os.getenv("ORTHANC_USER", "orthanc"), os.getenv("ORTHANC_PASS", "orthanc"))

    def get_instances(self):
        response = httpx.get(f"{self.url}/instances", auth=self.auth)
        response.raise_for_status()
        return response.json()

    def download_dicom(self, instance_id: str):
        response = httpx.get(f"{self.url}/instances/{instance_id}/file", auth=self.auth)
        response.raise_for_status()
        return response.content
        
    def upload_dicom(self, dicom_bytes: bytes):
        response = httpx.post(f"{self.url}/instances", auth=self.auth, content=dicom_bytes)
        response.raise_for_status()
        return response.json()

orthanc_client = OrthancClient()
