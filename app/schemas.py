from pydantic import BaseModel, root_validator, validator
from typing import List, Optional
from datetime import datetime
from .config import settings

class ResultOut(BaseModel):
    result_description: str

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    scheduler_time: Optional[datetime] = None
    lines: str

    @validator("scheduler_time", pre=True)
    def parse_scheduler_time(cls, value):
        # to be env var
        datetime_format = '%Y-%m-%dT%H:%M:%S'
        if type(value) == datetime:
            value = value.strftime(datetime_format)
        return datetime.strptime(
            value,
            datetime_format
        )
    @validator("lines")
    def parse_lines(cls, value):
        # to be env var or get the list automatic from the tfl api
        valid_lines = settings.valid_lines
        payload_lines = list(map(str.strip, value.split(',')))
        if len(set(payload_lines) - set(valid_lines)) != 0:
            raise ValueError('Non valid lines are found')
        return ','.join(payload_lines)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    lines: Optional[str] = None
    @root_validator
    def any_of(cls, v):
        if not any(v.values()):
            raise ValueError('Should provide update value for at least one field')
        return v

class TaskResponse(BaseModel):
    id: str
    created_at: datetime
    scheduler_time: datetime
    lines: str
    results: List[ResultOut]

    class Config:
        orm_mode = True