from . import schemas

def not_null_values_dict(task: schemas.TaskUpdate):
    return {key: value for key, value in task.dict().items() if value}