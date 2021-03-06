from database import *
from flask import Flask, request, redirect, render_template, Response, send_file, url_for, flash
from flask import session as login_session
import json
from functools import wraps
from datetime import datetime, timedelta 

app = Flask(__name__)
app.config['SECRET_KEY'] = "a;lfkdsjaflksdj"

UNITS = ["day", "week", "month"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def check_login_wrapper(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "language" not in login_session:
            login_session['language'] = 'Spanish'
            UNITS = ["dia", "semana", "mes"]
            WEEKDAYS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabados", "Domingo"]
        if "username" not in login_session:
            flash("Please login to see that page." if login_session["language"] == "English" else "Inicie sesión para ver esa página")
            return redirect(url_for('login'))
        if "language" not in login_session:
            login_session["language"] = "Spanish"
        return func(*args, **kwargs)
    return inner

@app.route('/changeLanguage', methods = ['POST'])
def changeLanguage():
    print("Changing language yoooo!")
    if "language" not in login_session or login_session['language'] == 'English':
        login_session['language'] = 'Spanish'
        UNITS = ["dia", "semana", "mes"]
        WEEKDAYS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabados", "Domingo"]
    else:
        login_session['language'] = 'English'
        UNITS = ["day", "week", "month"]
        WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return 'changed language'


@app.route('/changeLanguage', methods = ['GET'])
def changeLanguage2(return_url):
    if "language" not in login_session:
        login_session["language"] = "Spanish"

    if login_session['language'] == 'English':
        login_session['language'] = 'Spanish'
    else:
        login_session['language'] = 'English'
    return redirect(url_for(home))

@app.route('/')
@check_login_wrapper
def home():
    return redirect(url_for('daily_tasks_'))
    # return render_template("tasks.html", tasks=get_tasks())

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if 'id' in login_session:
        if login_session["language"] == "English":
            flash("Already logged in.")
        else:
            flash("Ya iniciado sesión.")
        return redirect(url_for("home"))
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        if username is None or password is None:
            if login_session["language"] == "English":
                flash("Missing Values.")
            else:
                flash("Valores faltantes.")
            return redirect(url_for('login'))
        if verify_password(username, password):
            user = get_user(username)
            login_session['username'] = user.username
            login_session['id'] = user.id
            login_session['is_admin'] = user.is_admin
            return redirect(url_for('home'))
            
        else:
            if login_session["language"] == "English":
                flash("Incorrect username/password combination.")
            else:
                flash("Combinación incorrecta de nombre de usuario / contraseña.")
            return redirect(url_for('login'))

@app.route("/logout")
def logout():
    lang = login_session['language']
    login_session.clear()
    login_session['language'] = lang
    if login_session["language"] == "English":
        flash("Successfully Logged Out.")
    else:
        flash("Desconectado correctamente.")
    return redirect(url_for('login'))

@app.route('/dashboard')
@check_login_wrapper
def dashboard():
    return render_template("dashboard.html", task_types = get_task_types(), units= UNITS)

@app.route("/add_user", methods = ['POST'])
@check_login_wrapper
def add_user():
    if not login_session['is_admin']:
        if login_session["language"] == "English":
            flash("Missing Values.")
        else:
            flash("Valores faltantes.")
        return redirect(url_for('login'))
    print("form", request.form)

    username = request.form['username']
    password = request.form['password']
    is_admin = "is_admin" in request.form
    if username is None or password is None:
        if login_session["language"] == "English":
            flash("Missing Values.")
        else:
            flash("Valores faltantes.")
        return redirect(url_for('dashboard'))

    create_user(username, password, is_admin)
    return redirect(url_for('dashboard'))

@app.route('/add_task_type',  methods = ['POST'])
@check_login_wrapper
def add_task_type():
    print("form", request.form)
    task_type = request.form['task_type']
    if task_type == "":
        flash("Cannot make a task without a name.")
        return redirect(url_for('dashboard'))
    elif get_task_type_by_name(task_type) != None:

        if login_session["language"] == "English":
            flash("Task by the name " + task_type + " already exists.")
        else:
            flash("La tarea con el nombre "+ task_type +" ya existe.")
        return redirect(url_for('dashboard'))
    required_fields = []
    optional_fields = []
    reminders = []
    for field in request.form:

        if field[:6] == "field_" and request.form[field] != "":
            count = field.split("_")[1]
            if "required_"+count in request.form:
                required_fields.append(request.form[field])
            else:
                optional_fields.append(request.form[field])
        elif field[:13] == "option_field_" and request.form[field] != "":
            count = field.split("_")[2]
            i = 1
            options = []
            print("option_{}_{}".format(count, i) in request.form, "option_{}_{}".format(count, i) )
            while "option_{}_{}".format(count, i) in request.form:
                if request.form["option_{}_{}".format(count, i)] != "":
                    options.append(request.form["option_{}_{}".format(count, i)])
                i += 1
            if "other_"+count in request.form:
                options.append("Other")
            print("options here", options)
            if "required_"+count in request.form:
                required_fields.append({request.form[field]:options})
            else:
                optional_fields.append({request.form[field]:options})
        elif field[:16] == "reminder_number_" and request.form[field] != "":
            count = field.split("_")[2]
            reminders.append(Reminder(int(request.form[field]), request.form["unit_{}".format(count)]))
            
    create_task_type(task_type, required_fields, optional_fields, reminders, request.form["task_color"])

    if login_session["language"] == "English":
        flash("Task Type: " + task_type + " created!")
    else:
        flash("Tipo de tarea: "+ task_type +" creado!")

    return redirect(url_for('dashboard'))

@app.route('/remove_task_type/<int:task_type_id>',  methods = ['POST'])
@check_login_wrapper
def remove_task_type_page(task_type_id):
    remove_task_type(task_type_id)
    return redirect(url_for('dashboard'))

@app.route('/tasks')
@check_login_wrapper
def tasks():
    return render_template("tasks.html", tasks=get_tasks(), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types())

@app.route('/daily_tasks')
@check_login_wrapper
def daily_tasks_():
    date = datetime.now().strftime("%Y-%m-%d")
    return render_template("daily_tasks.html", tasks=get_tasks_day(date), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), datestring=date,
        weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A"), overdue_tasks = get_overdue_tasks(date))

@app.route('/daily_tasks/<date>')
@check_login_wrapper
def daily_tasks(date):
    print("date", date)
    today_datestring = datetime.now().strftime("%Y-%m-%d")
    return render_template("daily_tasks.html", tasks=get_tasks_day(date), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), datestring=date,
        weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A"), overdue_tasks = get_overdue_tasks(today_datestring))


@app.route('/weekly_tasks/<date>')
@check_login_wrapper
def weekly_tasks(date):

    print("date", date)
    date_datetime = datetime.strptime(date, "%Y-%m-%d")
    monday =  date_datetime - timedelta(days = date_datetime.weekday())
    monday_datestr = monday.strftime("%Y-%m-%d")
    today_datestring = datetime.now().strftime("%Y-%m-%d")
    return render_template("weekly_tasks.html", tasks_by_day=get_tasks_week(monday_datestr), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), 
        datestrings = [(monday+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)], datestring=monday.strftime("%Y-%m-%d"),
        weekdays=WEEKDAYS, overdue_tasks = get_overdue_tasks(today_datestring))


@app.route('/weekly_tasks')
@check_login_wrapper
def weekly_tasks_(date):
    date = datetime.now().strftime("%Y-%m-%d")
    return weekly_tasks(date)

@app.route('/monthly_tasks/<date>')
@check_login_wrapper
def monthly_tasks(date):
    
    print("month date", date)
    # date_datetime = datetime.strptime(date, "%Y-%m-%d")
    # monday =  date_datetime - timedelta(days = date_datetime.weekday())
    # monday_datestr = monday.strftime("%Y-%m-%d")
    tasks_by_day, headers_by_day = get_tasks_month(date)
    legend = {}
    for day_notifications in tasks_by_day:
        for notification in day_notifications:
            legend[notification.task.task_type] = notification.task.color
    print("rendering month ", WEEKDAYS)
    today_datestring = datetime.now().strftime("%Y-%m-%d")
    return render_template("monthly_tasks.html", tasks_by_day=tasks_by_day, col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), 
        month =  datetime.strptime(date, "%Y-%m-%d").strftime("%B, %Y"), today_datestring= datetime.now().strftime("%Y-%m-%d"), datestring=date, headers_by_day=headers_by_day,
        weekdays=WEEKDAYS, legend=legend, overdue_tasks = get_overdue_tasks(today_datestring))

@app.route('/monthly_tasks')
@check_login_wrapper
def monthly_tasks_(date):
    date = datetime.now().strftime("%Y-%m-%d")
    return monthly_tasks(date)

@app.route('/task/<int:task_id>')
@check_login_wrapper
def task(task_id):
    if get_task(task_id) == None:
        flash("Task with id {} does not exist".format(task_id))
        return redirect(url_for('tasks'))
    task=get_task(task_id)
    print("name_to_item", {item.name:item for item in get_inventory()})
    return render_template("task.html", task=task, items_of_use=[get_inventory_item(item_id) for item_id in task.items_of_use], task_type=get_task_type_by_name(task.task_type), 
        units=UNITS,  name_to_item={item.name:item for item in get_inventory()})

@app.route('/toggle_complete_task/<int:task_id>', methods = ['POST'])
@check_login_wrapper
def toggle_complete_task(task_id):
    task=get_task(task_id)
    if task == None:
        return "task doesn't exist"
    if (task.completed):
        uncomplete_task(task_id)
    else:
        complete_task(task_id)
    return "done"

@app.route('/complete_task/<int:task_id>', methods = ['POST'])
@check_login_wrapper
def complete_task_page(task_id):
    complete_task(task_id)
    for field in request.form:
        if field[:4] == "item" and request.form[field] != "":
            item_id = field.split("_")[-1]
            item = get_inventory_item(item_id)
            if item == "None":
                flash("Invalid item")
            amount = float(request.form[field])
            update_inventory_item(item.name, -amount) 
            flash("Removed "+str(amount)+" "+item.unit.name+" of "+item.name+". Now has "+str(get_inventory_item(item_id).amount))
        if field[:10] == "added_item" and request.form[field] != "":
            input_id = field.split("_")[-1]
            item_name = request.form["added_item_"+input_id]

            item = get_inventory_item_by_name(item_name)
            if item == "None":
                flash("Invalid item")
            try:

                amount = float(request.form["added_amount_"+input_id])
                update_inventory_item(item.name, -amount) 
                flash("Removed "+str(amount)+" "+item.unit.name+" "+item.name+". Now has "+str(get_inventory_item(item_id).amount))
            except:
                flash("Invalid amount: "+request.form["added_amount_"+input_id])

    return render_template("task.html", task=get_task(task_id), task_type=get_task_type_by_name(get_task(task_id).task_type), units=UNITS)

@app.route('/uncomplete_task/<int:task_id>', methods = ['POST'])
@check_login_wrapper
def uncomplete_task_page(task_id):
    uncomplete_task(task_id)
    return render_template("task.html", task=get_task(task_id), task_type=get_task_type_by_name(get_task(task_id).task_type), units=UNITS)

@app.route('/add_task',  methods = ['GET', 'POST'])
@check_login_wrapper
def add_task():
    if request.method == 'GET':
        return render_template("add_task.html", task_types=get_task_types(), units=UNITS, inventory=get_inventory())
    else:
        print(request.form)
        task_type_name = request.form['task_type']
        task_type = get_task_type_by_name(task_type_name)
        due_date_str = request.form["due_date"]
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        description = request.form['description']
        patient_name = None
        if 'patient_name' in request.form:
            patient_name = request.form['patient_name']
        birthdate = None
        if 'birthdate' in request.form:
            birthdate = request.form['birthdate']
        dni = None
        if 'dni' in request.form:
            dni = request.form['dni']

        fields = {}
        reminders = []
        reminder_datestrings = []
        items_of_use = []
        for field in request.form:
            if field[:8] == "reminder":
                reminder_date_str = request.form[field]
                reminder_date = datetime.strptime(reminder_date_str, '%Y-%m-%d')
                reminders.append(reminder_date)
                reminder_datestrings.append(reminder_date_str)
            elif field[:4] == "item":
                inventory_item = get_inventory_item_by_name(request.form[field])
                if inventory_item == None:
                    if login_session["language"] == "English":
                        flash("Invalid item name: " + request.form[field])
                    else:
                        flash("Nombre de un articulo inválido: " + request.form[field])
                    return render_template("add_task.html", task_types=get_task_types(), inventory=get_inventory(), units=UNITS)
                items_of_use.append(inventory_item.id)
            elif field not in ["task_type", "due_date", "description", "patient_name", "birthdate", "dni"] and "_other" not in field: # TODO - don't let the use make custom fields using these names
                if request.form[field] == "Other":
                    fields[field] = request.form[field+"_other"]
                else:
                    fields[field] = request.form[field]

        succeeded, msg_eng, msg_spanish = create_task(get_user(login_session["username"]), due_date, description, patient_name, birthdate, dni, task_type_name, fields, reminders, reminder_datestrings, items_of_use)
        if succeeded:
            flash("Task added successfully!" if login_session["language"] == "English" else "Tarea agregado exitosamente!")
        else:
            flash(msg_eng if login_session["language"] == "English" else msg_spanish)
        return render_template("add_task.html", task_types=get_task_types(), inventory=get_inventory(), units=UNITS)

@app.route('/update_task/<int:task_id>',  methods = ['POST'])
@check_login_wrapper
def update_task_page(task_id):
    print("updating task", task_id)
    task_type_name = request.form['task_type']
    task_type = get_task_type_by_name(task_type_name)
    due_date_str = request.form["due_date"]
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    description = request.form["description"]
    fields = {}
    reminders = []
    reminder_datestrings = []

    for field in request.form:
        if field[:8] == "reminder":
            reminder_date_str = request.form[field]
            reminder_date = datetime.strptime(reminder_date_str, '%Y-%m-%d')
            reminders.append(reminder_date)
            reminder_datestrings.append(reminder_date_str)
        elif field not in ["task_type", "due_date", "description"]: # TODO - don't let the use make custom fields using these names
            fields[field] = request.form[field]
    update_task(task_id, due_date, description, task_type_name, fields, reminders, reminder_datestrings)
    flash("Task updated successfully!" if login_session["language"] == "English" else "Tarea actualizado exitosamente!") 
    print("updated", reminders)
    task = get_task(task_id)
    return render_template("task.html", task=task, items_of_use=[get_inventory_item(item_id) for item_id in task.items_of_use], task_type=get_task_type_by_name(task.task_type), units=UNITS,  inventory=get_inventory())

@app.route('/copy_task/<int:task_id>',  methods = ['GET', 'POST'])
@check_login_wrapper
def copy_task(task_id):
    task = get_task(task_id)
    return render_template("copy_task.html", task=task, task_type=get_task_type_by_name(task.task_type), items_of_use=[get_inventory_item(item_id) for item_id in task.items_of_use])


@app.route('/search',  methods = ['GET', 'POST'])
@check_login_wrapper
def search():
    if request.method == 'GET':
        return render_template("tasks.html")
    else:

        search_text = request.form['search']
        print(search_text)
        results = advanced_search(keywords = search_text.split(" "))
        print("results:", results)
        # return render_template("search_result.html", tasks=search_descr(search_text))
        return render_template("search.html", tasks=results, col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types())
    # tokenize search texts, then return results sorted in order of number of matches
    # can make a more advanced search - only searching in description, task_type, patient_name entries, etc


@app.route('/advanced_search',  methods = ['GET', 'POST'])
@check_login_wrapper
def advanced_search_page():
    if request.method == 'GET':
        return render_template("tasks.html")
    else:
        keywords = []
        if "keywords" in request.form:
            keywords = request.form['keywords'].split(" ")

        names = []
        if "names" in request.form:
            names = request.form['names'].split(" ")

        fields = []
        if "fields" in request.form:
            fields = request.form['fields'].split(" ")

        start_date = None
        if "start_date" in request.form:
            start_date = request.form['start_date']

        end_date = None
        if "end_date" in request.form:
            end_date = request.form['end_date']

        task_type = None
        if "task_type" in request.form:
            task_type = request.form["task_type"]

        completed = 'All'
        if "completed" in request.form:
            completed = request.form["completed"]

        results = advanced_search(keywords = keywords, names = names, fields = fields, start_date=start_date, end_date=end_date, task_type=task_type, completed=completed)
        # return render_template("search_result.html", tasks=search_descr(search_text))
        return render_template("search.html", tasks=results, col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(),
            keywords=" ".join(keywords), names = " ".join(names), fields = " ".join(fields), start_date=start_date, end_date=end_date, task_type=task_type)

# need to be able to filter and sort tasks on task page using javascript

@app.route('/inventory')  
@check_login_wrapper
def inventory():
    print("inventory", get_inventory())
    inventory_by_types = {}
    for inv_item in get_inventory():
        if inv_item.inventory_type.name not in inventory_by_types:
            inventory_by_types[inv_item.inventory_type.name] = []
        inventory_by_types[inv_item.inventory_type.name].append(inv_item)
    print("invent by types", inventory_by_types)
    return render_template("inventory.html", inventory=get_inventory(), inventory_by_types=inventory_by_types, units = get_units(), inv_types = get_inventory_types())

@app.route('/add_unit', methods = ['POST'])  
@check_login_wrapper
def add_unit_page():
    if "abbreviation" not in request.form or request.form["abbreviation"] == "":
        abbreviation = request.form["unit_name"]
    else:
        abbreviation = request.form["abbreviation"]
    add_unit(request.form["unit_name"], abbreviation)
    return redirect(url_for('inventory'))

@app.route('/add_inventory_type', methods = ['POST'])  
@check_login_wrapper
def add_inventory_type_page():
    add_inventory_type(request.form["type_name"])
    return redirect(url_for('inventory'))

@app.route('/add_item', methods = ['POST'])  
@check_login_wrapper
def add_item_page():
    unit = get_unit_by_name(request.form["unit_name"])
    inv_type = get_inventory_type_by_name(request.form["type_name"])
    add_inventory_item(request.form["item_name"], float(request.form["amount"]), unit, inv_type, float(request.form["danger_amount"]), float(request.form["buy_more_amount"]))
    return redirect(url_for('inventory'))

@app.route('/set_item', methods = ['POST'])  
@check_login_wrapper
def set_item_amount_page():
    set_inventory_item(request.form["item_name"], float(request.form["amount"]))
    return redirect(url_for('inventory'))

@app.route('/change_item', methods = ['POST'])  
@check_login_wrapper
def change_item_amount_page():
    succeed, message_english, message_spanish = update_inventory_item(request.form["item_name"], float(request.form["amount"]))
    if not succeed:
        if login_session['language'] == "English":
            flash(message_english)
        else:
            flash(message_spanish)
    return redirect(url_for('inventory'))


if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True)
