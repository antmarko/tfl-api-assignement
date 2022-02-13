from typing import List
import requests

class Disruption(object):
    @staticmethod
    def get_disruption_details(lines: str)->List[str]:
        response = requests.get(f"https://api.tfl.gov.uk/Line/{lines}/Disruption")
        response_json = response.json()
        result = [elem['description'] for elem in response_json]
        return list(set(result))