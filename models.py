from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, PickleType
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from passlib.apps import custom_app_context as pwd_security

Base = declarative_base()
TASK_TYPES = ['prescription', 'appointment']

class Reminder():
    def __init__(self, amount, unit):
        self.amount = amount
        self.unit = unit

class Notification():
    def __init__(self, task, is_reminder):
        self.task = task
        self.is_reminder = is_reminder

class HeaderNumber():
    def __init__(self, number, is_month, datestring):
        self.number = number
        self.is_month = is_month
        self.datestring = datestring


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
    reminders = Column(PickleType) # list of datetimes
    reminder_datestrings = Column(PickleType) # list of datetimes
    color = Column(String)

class TaskType(Base):
    __tablename__ = "task_types"
    id = Column(Integer, primary_key=True)
    task_type = Column(String)
    required_fields = Column(PickleType) # list of strings that are required keys in the fields entry of a task
    optional_fields = Column(PickleType) # list of strings that are allowed but not required keys in the fields entry of a task
    reminders = Column(PickleType) # list of dates for when reminders should go off
    color = Column(String)

# Inventory Models
class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    abbreviation = Column(String)

class InventoryType(Base):
    __tablename__ = "inventory_type"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class InventoryItem(Base):
    __tablename__ = "inventory_item"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount = Column(Float)
    unit = Column(PickleType)
    inventory_type = Column(PickleType)
    danger_amount = Column(Float)
    buy_more_amount = Column(Float)


