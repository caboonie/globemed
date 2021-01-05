from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, PickleType
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from passlib.apps import custom_app_context as pwd_security

Base = declarative_base()
TASK_TYPES = ['prescription', 'appointment']

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    password_hash = Column(String)
    username = Column(String)
    is_admin = Column(Boolean)

    def hash_password(self, password):
        self.password_hash = pwd_security.encrypt(password)
    def verify_password(self, password):
        return pwd_security.verify(password, self.password_hash)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    task_type = Column(String, default="Generic")
    creator_id = Column(Integer)
    created_datetime = Column(DateTime)
    created_datestring = Column(String)
    due_datetime = Column(DateTime)
    due_datestring = Column(String)
    description = Column(String)
    completed = Column(Boolean) # completed or not
    fields = Column(PickleType) # dictionary of strings to strings

class TaskType(Base):
    __tablename__ = "task_types"
    id = Column(Integer, primary_key=True)
    task_type = Column(String)
    required_fields = Column(PickleType) # list of strings that are required keys in the fields entry of a task
    optional_fields = Column(PickleType) # list of strings that are allowed but not required keys in the fields entry of a task
