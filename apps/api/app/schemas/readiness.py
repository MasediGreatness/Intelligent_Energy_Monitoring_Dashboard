from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ready"]
    database: Literal["ready"]
    migrations: Literal["at_head"]
    revision: str
