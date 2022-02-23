from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from .database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), 
                        nullable=False, server_default=text("DATE_TRUNC('second', NOW())"))
    scheduler_time = Column(TIMESTAMP(timezone=False),
                            nullable=False, server_default=text("DATE_TRUNC('second', NOW())"))
    lines = Column(String, nullable=False)
    results = relationship("Result")

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, nullable=False)
    task_id = Column(String, ForeignKey('tasks.id', ondelete="CASCADE"), nullable=False)
    result_description = Column(String, nullable=False)

