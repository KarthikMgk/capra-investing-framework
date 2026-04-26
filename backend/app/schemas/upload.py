from pydantic import BaseModel


class UploadResponse(BaseModel):
    status: str = "ok"
    batch_id: str
