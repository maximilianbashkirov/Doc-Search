from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    id: str
    rubrics: list[str]
    text: str
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)
