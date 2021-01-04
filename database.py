from models import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///tasks.db?check_same_thread=False')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Interactions

def create_user(name,secret_word, is_admin):
    user = User(username=name, is_admin=is_admin)
    user.hash_password(secret_word)
    session.add(user)
    session.commit()
    return user

def get_user(username):
    return session.query(User).filter_by(username=username).first()

def get_user_id(id_num):
    return session.query(User).filter_by(id=id_num).first()

def verify_password(username, password):
    user = session.query(User).filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    return True

user = session.query(User).filter_by(username='admin').first()
if not user:
    create_user('admin','nimda', True)

# Task Type Interactions

def create_task_type(task_type, required_fields, optional_fields):
    task_type = TaskType(task_type=task_type, required_fields=required_fields, optional_fields=optional_fields)
    session.add(task_type)
    session.commit()

def get_task_types():
    return session.query(TaskType).all()

def get_task_type(task_type_id):
    return session.query(TaskType).filter_by(id=task_type_id).first()

def get_task_type_by_name(name):
    return session.query(TaskType).filter_by(task_type=name).first()


task_type = get_task_type_by_name("appointment")
if not task_type:
    create_task_type("appointment", ["patient_name"], [])

# Task Interactions

def create_task(user, due_date, description, task_type, fields=None):
    if fields == None:
        fields = {}
    task_type_meta = get_task_type_by_name(task_type)
    if not task_type_meta:
        return False, "Not a valid task type"
    elif not all([field in fields for field in task_type_meta.required_fields]):
        return False, "Missing required_fields: " + " ".join([field for field in task_type_meta.required_fields if field not in fields])
    elif not all([field in task_type_meta.required_fields+task_type_meta.optional_fields for field in fields]):
        return False, "Contains extraneous fields: " + " ".join([field for field in fields if field not in task_type_meta.required_fields+task_type_meta.optional_fields])

    task = Task(creator_id=user.id, created_datetime=datetime.now(), created_datestring=datetime.now().strftime("%m/%d/%Y"), due_datetime=due_date, due_datestring=due_date.strftime("%m/%d/%Y"), 
        description=description, task_type=task_type, fields=fields)
    
    session.add(task)
    session.commit()
    return True, task

# def create_appointment(user, due_date, description, patient_name):
#     task = Appointment(creator_id=user.id, created_datetime=datetime.now(), created_datestring=datetime.now().strftime("%m/%d/%Y"), due_datetime=due_date, due_datestring=due_date.strftime("%m/%d/%Y"), 
#         description=description, task_type='appointment', patient_name=patient_name)
    
#     session.add(task)
#     session.commit()
#     return task



def get_tasks():
    return session.query(Task).all()

def get_task(task_id):
    return session.query(Task).filter_by(id=task_id).first()

def search_descr(search_text):
    filtered_tasks = []
    for task in get_tasks():
        if search_text in task.description:
            filtered_tasks.append(task)
    return filtered_tasks

create_task(session.query(User).filter_by(username='admin').first(), datetime.now(), "test", "appointment", {"patient_name":"caleb"})
# create_task(session.query(User).filter_by(username='admin').first(), datetime.now(), "test2", "prescription")
# create_appointment(session.query(User).filter_by(username='admin').first(), datetime.now(), "tes;sdlkjf;ladskjfl;asdlkldjfklsdfj kdjklfsdj;lkfjksdl akdlfjkdsj dlakfjdskljf slkdfjlkdsjfdslkj sdflkjdslkjt", "caleb")