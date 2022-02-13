from fastapi import Body, FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from .. import models, schemas, utils

router = APIRouter(
    prefix="/tasks",
    tags=['Tasks']
)

@router.get("/", response_model=List[schemas.TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    return tasks

@router.get("/{id}", response_model=schemas.TaskResponse)
async def get_task(id: int, response: Response, db: Session = Depends(get_db)):
    returned_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not returned_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task with id: {id} not found")
    return returned_task

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.TaskResponse)
async def create_task(new_task: schemas.TaskCreate, db: Session = Depends(get_db)):
    if not new_task.scheduler_time:
        new_task_model = models.Task(lines=new_task.lines)
    else:
        new_task_model = models.Task(**new_task.dict())
    db.add(new_task_model)
    db.commit()
    db.refresh(new_task_model)
    return new_task_model

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: int, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    if task_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    task_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{id}", response_model=schemas.TaskResponse)
async def update_task(id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    returned_task = task_query.first()
    if returned_task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    if returned_task.scheduler_time <= datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f"Task with id: {id} is already executed")
    # dynamic update query based on given fields
    task_query.update(utils.not_null_values_dict(task), synchronize_session=False)
    db.commit()
    return task_query.first()