from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
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

class Appointment(Task):
    patient_name = Column(String)

class Prescription(Task):
    product_name = Column(String)
    amount = Column(Float)
    units = Column(String)
    