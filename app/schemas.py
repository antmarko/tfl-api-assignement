from pydantic import BaseModel, root_validator, validator
from typing import Optional
from datetime import datetime

class Task(BaseModel):
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
        valid_lines = [
            "bakerloo",
            "central",
            "circle",
            "district",
            "hammersmith-city",
            "jubilee",
            "metropolitan",
            "northern",
            "piccadilly",
            "victoria",
            "waterloo-city"
        ]
        payload_lines = list(map(str.strip, value.split(',')))
        if len(set(payload_lines) - set(valid_lines)) != 0:
            raise ValueError('Not valid lines are found')
        return ','.join(payload_lines)

class UpdateTask(Task):
    lines: Optional[str] = None
    @root_validator
    def any_of(cls, v):
        if not any(v.values()):
            raise ValueError('Should provide update value for at least one field')
        return v