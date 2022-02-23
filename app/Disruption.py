from typing import List
import requests
from sqlalchemy.orm import Session
from sqlalchemy.engine.base import Engine
from . import models

class Disruption(object):
    @staticmethod
    def get_disruption_results(lines: str)->List[str]:
        response = requests.get(f"https://api.tfl.gov.uk/Line/{lines}/Disruption")
        response_json = response.json()
        result = [elem['description'] for elem in response_json]
        return list(set(result))

    @staticmethod
    def save_disruption_results(task_id: str, results: List, engine: Engine)->None:
        with Session(engine) as session:
            try:
                for description in results:
                    new_result_model = models.Result(result_description=description, task_id=task_id)
                    session.add(new_result_model)
                session.commit()
            except Exception as e:
                print(f"Could not store the results of task {task_id} to database", e)