import imp
from time import sleep
from hashlib import new
from fastapi import Body, FastAPI, Response, status, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db
from datetime import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def not_null_values_dict(task: schemas.UpdateTask):
    return {key: value for key, value in task.dict().items() if value}

@app.get("/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    return {"data": tasks}

@app.get("/tasks/{id}")
async def get_task(id: int, response: Response, db: Session = Depends(get_db)):
    returned_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not returned_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task with id: {id} not found")
    return {"task_details": returned_task}

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(new_task: schemas.Task, db: Session = Depends(get_db)):
    if not new_task.scheduler_time:
        new_task_model = models.Task(lines=new_task.lines)
    else:
        new_task_model = models.Task(**new_task.dict())
    db.add(new_task_model)
    db.commit()
    db.refresh(new_task_model)
    return {"data": new_task_model}

@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: int, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    if task_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    task_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.patch("/tasks/{id}")
async def update_task(id: int, task: schemas.UpdateTask, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    returned_task = task_query.first()
    if returned_task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    if returned_task.scheduler_time <= datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f"Task with id: {id} is already executed")
    # dynamic update query based on given fields
    task_query.update(not_null_values_dict(task), synchronize_session=False)
    db.commit()
    return {"data": task_query.first()}