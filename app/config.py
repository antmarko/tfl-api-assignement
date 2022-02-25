from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    valid_lines: List[str]
    tfl_line_endpoint_url: str
    disruption_endpoint_suffix: str

    class Config:
        env_file = ".env"

settings = Settings()