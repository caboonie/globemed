from models import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta 

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

def create_task_type(task_type, required_fields, optional_fields, reminders, color):
    task_type = TaskType(task_type=task_type, required_fields=required_fields, optional_fields=optional_fields, reminders=reminders, color=color)
    session.add(task_type)
    session.commit()

def remove_task_type(task_type_id):
    task_type = get_task_type(task_type_id)
    if task_type == None:
        return
    print("removing", task_type.task_type)
    session.delete(task_type)
    session.commit()



def get_task_types():
    return session.query(TaskType).all()

def get_task_type(task_type_id):
    return session.query(TaskType).filter_by(id=task_type_id).first()

def get_task_type_by_name(name):
    return session.query(TaskType).filter_by(task_type=name).first()


# remove_task_type(get_task_type_by_name("order supplies").id)
task_type = get_task_type_by_name("appointment")
if not task_type:
    create_task_type("appointment", ["patient_name"], [], [], "blue")

# Task Interactions

def clean_fields(task_type_meta):
    return ([field if type(field) == str else list(field)[0] for field in task_type_meta.required_fields],
            [field if type(field) == str else list(field)[0] for field in task_type_meta.optional_fields])

def create_task(user, due_date, description, task_type, fields, reminders, reminder_datestrings, items_of_use):
    task_type_meta = get_task_type_by_name(task_type)
    required_fields, optional_fields = clean_fields(task_type_meta)
    if not task_type_meta:
        return False, "Not a valid task type", "Tipo de tarea inválido"
    elif not all([field in fields for field in required_fields]):
        return False, "Missing required_fields: " + " ".join([field for field in required_fields if field not in fields]), "Campos necesarios que faltan: " + " ".join([field for field in required_fields if field not in fields])
    elif not all([field in required_fields+optional_fields for field in fields]):
        return False, "Contains extraneous fields: " + " ".join([field for field in fields if field not in required_fields+optional_fields]), "Se incluye campos extraños: " + " ".join([field for field in fields if field not in required_fields+optional_fields])

    task = Task(creator_id=user.id, created_datetime=datetime.now(), created_datestring=datetime.now().strftime("%Y-%m-%d"), due_datetime=due_date, due_datestring=due_date.strftime("%Y-%m-%d"), 
        description=description, task_type=task_type, completed=False, fields=fields, reminders=reminders, reminder_datestrings=reminder_datestrings, color=task_type_meta.color, 
        items_of_use=items_of_use)
    
    session.add(task)
    session.commit()
    return True, task, task

def update_task(task_id, due_date, description, task_type, fields, reminders, reminder_datestrings):
    task = session.query(Task).filter_by(id=task_id).first()
    task.due_date = due_date
    task.description = description
    task.task_type = task_type
    task.fields = fields
    task.reminders = reminders
    task.reminder_datestrings = reminder_datestrings
    session.commit()

# def create_appointment(user, due_date, description, patient_name):
#     task = Appointment(creator_id=user.id, created_datetime=datetime.now(), created_datestring=datetime.now().strftime("%m/%d/%Y"), due_datetime=due_date, due_datestring=due_date.strftime("%m/%d/%Y"), 
#         description=description, task_type='appointment', patient_name=patient_name)
    
#     session.add(task)
#     session.commit()
#     return task

def complete_task(task_id):
    task = session.query(Task).filter_by(id=task_id).first()
    task.completed = True
    session.commit()

def uncomplete_task(task_id):
    task = session.query(Task).filter_by(id=task_id).first()
    task.completed = False
    session.commit()    


def get_tasks():
    return session.query(Task).all()

def get_task(task_id):
    return session.query(Task).filter_by(id=task_id).first()

def get_tasks_day(date):
    tasks = []
    for task in get_tasks():
        print("task due", task.due_datestring, task.reminder_datestrings, date)
        if task.due_datestring == date or date in task.reminder_datestrings:
            tasks.append(task)
    return tasks

def get_tasks_week(monday_date):
    tasks_by_day = []
    monday_datetime = datetime.strptime(monday_date, "%Y-%m-%d")
    for i in range(7):
        day_datetime = monday_datetime + timedelta(days=i)
        date = day_datetime.strftime("%Y-%m-%d")
        tasks = []
        for task in get_tasks():
            print("task due", task.due_datestring, task.reminder_datestrings, date)
            if task.due_datestring == date or date in task.reminder_datestrings:
                tasks.append(task)
        tasks_by_day.append(tasks)
    print("tasks_by_day", tasks_by_day)
    return tasks_by_day

def get_tasks_month(date):
    tasks_by_day = []
    headers_by_day = []
    first_datetime = datetime.strptime(date, "%Y-%m-%d")
    first_datetime = first_datetime - timedelta(days = (first_datetime.day-1))
    first_monday = first_datetime - timedelta(days = first_datetime.weekday())
    for i in range(35):
        day_datetime = first_monday + timedelta(days=i)
        date = day_datetime.strftime("%Y-%m-%d")
        tasks = []
        for task in get_tasks():
            print("task due", task.due_datestring, task.reminder_datestrings, date)
            if task.due_datestring == date:
                tasks.append(Notification(task, False))
            if date in task.reminder_datestrings:
                tasks.append(Notification(task, True))
        tasks_by_day.append(tasks)
        headers_by_day.append(HeaderNumber(day_datetime.day, day_datetime.month == first_datetime.month, date))

    print("tasks_by_day", tasks_by_day)
    return tasks_by_day, headers_by_day

def search_descr(search_text):
    filtered_tasks = []
    for task in get_tasks():
        if search_text in task.description:
            filtered_tasks.append(task)
    return filtered_tasks

def advanced_search(keywords=[], names=[], fields=[], start_date=None, end_date=None, task_type=None, completed=None):
    ranked_tasks = []
    for task in get_tasks():
        if start_date:
            if datetime.strptime(start_date, "%Y-%m-%d") > task.due_datetime:
                continue
        if end_date:
            if datetime.strptime(end_date, "%Y-%m-%d") < task.due_datetime:
                continue
        if task_type and task_type != task.task_type:
            continue
        if completed and (completed != "All" and ((completed == "True" and not task.completed) or (completed == "False" and task.completed))):
            continue
        matches = 0
        for keyword in keywords:
            if keyword.lower() in "".join([task.description.lower(), task.task_type.lower()]+[field.lower() for field in task.fields]+[task.fields[field].lower() for field in task.fields]):
                matches += 1
        name_field = None
        if "name" in task.fields:
            name_field = "name"
        elif "Name" in task.fields:
            name_field = "Name"
        if name_field:
            for name in names:
                if name.lower() in task.fields[name_field].lower():
                    matches += 1
        for field in fields:
            if field.lower() in [key.lower() for key in task.fields]:
                matches += 1
        if matches > 0:
            ranked_tasks.append((task, matches))
    ranked_tasks.sort(key=lambda x:-x[1])
    return [pair[0] for pair in ranked_tasks]


# create_task(session.query(User).filter_by(username='admin').first(), datetime.now(), "test", "appointment", {"Patient name":"caleb"}, [], [])
# create_task(session.query(User).filter_by(username='admin').first(), datetime.now(), "test2", "prescription")
# create_appointment(session.query(User).filter_by(username='admin').first(), datetime.now(), "tes;sdlkjf;ladskjfl;asdlkldjfklsdfj kdjklfsdj;lkfjksdl akdlfjkdsj dlakfjdskljf slkdfjlkdsjfdslkj sdflkjdslkjt", "caleb")


# Inventory Interface

def add_unit(unit_name, abbreviation=None):
    if abbreviation == None:
        abbreviation = unit_name
    unit = Unit(name=unit_name, abbreviation=abbreviation)
    session.add(unit)
    session.commit()

def get_unit(unit_id):
    return session.query(Unit).filter_by(id=unit_id).first()

def get_unit_by_name(unit_name):
    return session.query(Unit).filter_by(name=unit_name).first()

def get_units():
    return session.query(Unit).all()

if get_unit_by_name("grams") == None:
    add_unit("grams", "g")


def add_inventory_type(name):
    inv_type = InventoryType(name=name)
    session.add(inv_type)

def get_inventory_type(type_id):
    return session.query(InventoryType).filter_by(id=type_id).first()

def get_inventory_type_by_name(type_name):
    return session.query(InventoryType).filter_by(name=type_name).first()

def get_inventory_types():
    return session.query(InventoryType).all()

if get_inventory_type_by_name("Pharmacy") == None:
    add_inventory_type("Pharmacy")


def get_inventory_item(id):
    return session.query(InventoryItem).filter_by(id=id).first()

def get_inventory_item_by_name(name):
    return session.query(InventoryItem).filter_by(name=name).first()

def get_inventory():
    return session.query(InventoryItem).all()

def add_inventory_item(name, init_amount, unit_object, inv_type, danger_amount, buy_more_amount):
    # print("check", get_inventory_item_by_name(name), get_inventory_item_by_name(name)==None, type(get_inventory_item_by_name(name)))
    if get_inventory_item_by_name(name) != None:
        return False, "Already added"
    item = InventoryItem(name=name, amount=init_amount, unit=unit_object, inventory_type=inv_type, danger_amount=danger_amount, buy_more_amount=buy_more_amount)
    session.add(item)
    session.commit()
    return True, "Successfully added"

def update_inventory_item(item_name, amount_diff):
    item = get_inventory_item_by_name(item_name)
    if item == None:
        return False, "Invalid Item Name","Nombre de artículo no válido"
    item.amount = max(0, item.amount + amount_diff)
    session.commit()
    return True, "no msg", "no msg"

def set_inventory_item(item_name, amount):
    item = get_inventory_item_by_name(item_name)
    item.amount = amount
    session.commit()

if get_inventory_item_by_name("Tylenol") == None:
    print("adding Tylenol")
    print(add_inventory_item("Tylenol", 100.5, get_unit_by_name("grams"), get_inventory_type_by_name("Pharmacy"), 100, 150))
print("Tylenol there?", get_inventory_item_by_name("Tylenol"))


