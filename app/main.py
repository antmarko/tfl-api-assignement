import imp
import psycopg2
from time import sleep
from psycopg2.extras import RealDictCursor
from hashlib import new
from typing import Optional
from fastapi import Body, FastAPI, Response, status, HTTPException
from pydantic import BaseModel, root_validator, validator
from datetime import datetime
from random import randrange


app = FastAPI()

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

def create_dynamic_update_query(task: UpdateTask):
    task_dict = task.dict()
    update_fields = [field for field in task_dict.keys() if task_dict[field]]
    update_values = [task_dict[key] for key in update_fields]
    dynamic_query = """UPDATE tasks SET %s WHERE ID = %s  RETURNING *""" \
                    % (', '.join("%s = %%s" % u for u in update_fields), '%s')
    return dynamic_query, update_values

while True:
    try:
        conn = psycopg2.connect(
            host='localhost', 
            database='fastapi', 
            user='postgres', 
            password='postgres',
            cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Succesfully connected to database")
        break
    except Exception as error:
        print("Failed to connect to the database")
        print("Error: ", error)
    sleep(5)

@app.get("/tasks")
async def get_tasks():
    cursor.execute("""SELECT * FROM tasks""")
    tasks = cursor.fetchall()
    return {"data": tasks}

@app.get("/tasks/{id}")
async def get_task(id: int, response: Response):
    cursor.execute("""SELECT * FROM tasks WHERE ID = %s""", (id,))
    returned_task = cursor.fetchone()
    if not returned_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task with id: {id} not found")
    return {"task_details": returned_task}

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(new_task: Task):
    if not new_task.scheduler_time:
        cursor.execute("""INSERT INTO tasks (lines) VALUES (%s) RETURNING *""",
        (new_task.lines,))
    else:
        cursor.execute("""INSERT INTO tasks (scheduler_time, lines) VALUES (%s, %s) RETURNING *""",
        (new_task.scheduler_time, new_task.lines))        
    returned_task = cursor.fetchone()
    conn.commit()
    return {"data": returned_task}

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: int):
    cursor.execute("""DELETE FROM tasks WHERE ID = %s  RETURNING *""", (id,))
    returned_task = cursor.fetchone()
    conn.commit()
    if returned_task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.patch("/tasks/{id}")
async def update_task(id: int, task: UpdateTask):
    # dynamic update query based on given fields
    dynamic_query, update_values = create_dynamic_update_query(task)
    cursor.execute(dynamic_query, (*update_values, id))
    returned_task = cursor.fetchone()
    conn.commit()
    if returned_task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    if returned_task['scheduler_time'] <= datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f"Task with id: {id} is already executed")
    return {"data": returned_task}