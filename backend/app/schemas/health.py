from typing import Literal

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: Literal["healthy"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "unready"]
    database: Literal["connected", "disconnected"]
