from fastapi import Body, FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from typing import List
from datetime import datetime
from ..database import get_db, engine
from .. import models, schemas, utils
from ..Disruption import Disruption 

router = APIRouter(
    prefix="/tasks",
    tags=['Tasks']
)

def fetch_and_store_results(task_id: str, lines: str)->None:
    results = Disruption.get_disruption_results(lines)
    Disruption.save_disruption_results(task_id, results, engine)

@router.on_event('startup')
async def start_schedule():
    global scheduler
    default_jobstore = {'default': SQLAlchemyJobStore(tablename='apscheduler_jobs', engine=engine)}
    scheduler = BackgroundScheduler(jobstores=default_jobstore, timezone=None)
    scheduler.start()

@router.on_event("shutdown")
async def quit_schedule():
    """
    An Attempt at Shutting down the schedule to avoid orphan jobs
    """
    global scheduler
    scheduler.shutdown()

@router.get("/", response_model=List[schemas.TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    return tasks

@router.get("/{id}", response_model=schemas.TaskResponse)
async def get_task(id: str, response: Response, db: Session = Depends(get_db)):
    returned_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not returned_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task with id: {id} not found")
    # temp code
    global scheduler
    job = scheduler.get_job(id, jobstore='default')
    return returned_task

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.TaskResponse)
async def create_task(new_task: schemas.TaskCreate, db: Session = Depends(get_db)):
    if new_task.scheduler_time and new_task.scheduler_time <= datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f"Provide a datetime greater than the current one")
    global scheduler
    unique_id = utils.create_uuid()
    if not new_task.scheduler_time:
        new_task_model = models.Task(lines=new_task.lines, id=unique_id)
        job = scheduler.add_job(fetch_and_store_results, 
                            jobstore='default', 
                            id=unique_id, 
                            kwargs={'task_id': unique_id, 'lines': new_task.lines}
                            )
    else:
        new_task_model = models.Task(**new_task.dict(), id=unique_id)
        job = scheduler.add_job(fetch_and_store_results, 
                            jobstore='default',
                            id=unique_id,
                            trigger='date', 
                            next_run_time=new_task.scheduler_time, 
                            kwargs={'task_id': unique_id, 'lines': new_task.lines}
                            )
    db.add(new_task_model)
    db.commit()
    db.refresh(new_task_model)
    return new_task_model

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(id: str, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    if task_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    # delete the job from apscheduler table too if not executed yet
    global scheduler
    apscheduler_job = scheduler.get_job(id)
    if apscheduler_job:
        scheduler.remove_job(id)
    task_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch("/{id}", response_model=schemas.TaskResponse)
async def update_task(id: str, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    returned_task = task_query.first()
    if returned_task == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f"Task with id: {id} doesnt exist")
    if returned_task.scheduler_time <= datetime.now():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f"Task with id: {id} is or has been already executed")
    # dynamic update query based on given fields
    task_query.update(utils.not_null_values_dict(task), synchronize_session=False)
    db.commit()
    # update/reschedule apscheduler job
    global scheduler
    if task.scheduler_time:
        scheduler.reschedule_job(id, 
                                 jobstore='default', 
                                 trigger='date', 
                                 run_date=task.scheduler_time)
    if task.lines:
        scheduler.modify_job(id, 
                            jobstore='default', 
                            kwargs={'task_id': id, 'lines': task.lines}
                            )
    return task_query.first()