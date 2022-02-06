from hashlib import new
import imp
from typing import Optional
from fastapi import Body, FastAPI, Response, status, HTTPException
from pydantic import BaseModel, root_validator, validator
from datetime import datetime
from random import randrange

app = FastAPI()

my_tasks = []

def find_task(id):
    for t in my_tasks:
        if t['id'] == id:
            return t

def find_index_task(id):
    for i,t in enumerate(my_tasks):
        if t['id'] == id:
            return i

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

@app.get("/tasks")
async def get_tasks():
    return {"data": my_tasks}

@app.get("/tasks/{id}")
async def get_task(id: int, response: Response):
    task = find_task(id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task with id: {id} not found")
    return {"task_details": task}

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(new_task: Task):
    # validate date format: Done in pydantic
    # split string containing the lines if more than one: Done in pydantic
    # validate that the line(s) are valid: Done in pydantic
    new_task_dict = new_task.dict()
    new_task_dict['id'] = randrange(1, 10000000)
    my_tasks.append(new_task_dict)
    return new_task_dict

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: int):
    index = find_index_task(id)
    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    my_tasks.pop(index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.patch("/tasks/{id}")
async def update_task(id: int, task: UpdateTask):
    index = find_index_task(id)
    if index == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    if my_tasks[index]['scheduler_time'] <= datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f"Task with id: {id} is already executed")
    stored_task_data = my_tasks[index]
    stored_task_model = Task(**stored_task_data)
    update_data = task.dict(exclude_unset=True)
    update_data['id'] = id
    updated_task = stored_task_model.copy(update=update_data)
    my_tasks[index] = updated_task.dict()
    return {"data": my_tasks[index]}