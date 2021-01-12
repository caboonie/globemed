from database import *
from flask import Flask, request, redirect, render_template, Response, send_file, url_for, flash
from flask import session as login_session
import json
from functools import wraps
from datetime import datetime, timedelta 

app = Flask(__name__)
app.config['SECRET_KEY'] = "a;lfkdsjaflksdj"

UNITS = ["day", "week", "month"]

def check_login_wrapper(func):
    @wraps(func)
    def inner(*args, **kwargs):
        print("here")
        if "username" not in login_session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner


@app.route('/')
@check_login_wrapper
def home():
    return redirect(url_for('tasks'))
    # return render_template("tasks.html", tasks=get_tasks())

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if 'id' in login_session:
        flash("Already logged in.")
        return redirect(url_for("home"))
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        if username is None or password is None:
            flash("Missing Values")
            return redirect(url_for('login'))
        if verify_password(username, password):
            user = get_user(username)
            login_session['username'] = user.username
            login_session['id'] = user.id
            login_session['is_admin'] = user.is_admin
            return redirect(url_for('home'))
            
        else:
            flash("Incorrect email/password combination")
            return redirect(url_for('login'))

@app.route("/logout")
def logout():
    login_session.clear()
    flash("Successfully Logged Out")
    return redirect(url_for('home'))

@app.route('/dashboard')
@check_login_wrapper
def dashboard():
    return render_template("dashboard.html", task_types = get_task_types(), units= UNITS)

@app.route("/add_user", methods = ['POST'])
@check_login_wrapper
def add_user():
    if not login_session['is_admin']:
        flash("Missing Values")
        return redirect(url_for('login'))
    print("form", request.form)

    username = request.form['username']
    password = request.form['password']
    is_admin = "is_admin" in request.form
    if username is None or password is None:
        flash("Missing Required Values")
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
        flash("Task by the name " + task_type + " already exists.")
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
            if "other"+count in request.form:
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
    flash("Task Type: " + task_type + " created!")

    return redirect(url_for('dashboard'))

@app.route('/tasks')
@check_login_wrapper
def tasks():
    return render_template("tasks.html", tasks=get_tasks(), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types())

@app.route('/daily_tasks')
@check_login_wrapper
def daily_tasks_():
    date = datetime.now().strftime("%Y-%m-%d")
    return render_template("daily_tasks.html", tasks=get_tasks_day(date), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), datestring=date)

@app.route('/daily_tasks/<date>')
@check_login_wrapper
def daily_tasks(date):
    print("date", date)
    return render_template("daily_tasks.html", tasks=get_tasks_day(date), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), datestring=date)


@app.route('/weekly_tasks/<date>')
@check_login_wrapper
def weekly_tasks(date):

    print("date", date)
    date_datetime = datetime.strptime(date, "%Y-%m-%d")
    monday =  date_datetime - timedelta(days = date_datetime.weekday())
    monday_datestr = monday.strftime("%Y-%m-%d")
    return render_template("weekly_tasks.html", tasks_by_day=get_tasks_week(monday_datestr), col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), 
        datestrings = [(monday+timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)],
        weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])


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

    return render_template("monthly_tasks.html", tasks_by_day=tasks_by_day, col_strings = ["Due Date"], col_vars = ["due_datestring"], task_types=get_task_types(), 
        month =  datetime.strptime(date, "%Y-%m-%d").strftime("%B, %Y"), datestring=date, headers_by_day=headers_by_day,
        weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], legend=legend)


@app.route('/task/<int:task_id>')
@check_login_wrapper
def task(task_id):
    return render_template("task.html", task=get_task(task_id))

@app.route('/complete_task/<int:task_id>', methods = ['POST'])
@check_login_wrapper
def complete_task_page(task_id):
    complete_task(task_id)
    return render_template("task.html", task=get_task(task_id))

@app.route('/uncomplete_task/<int:task_id>', methods = ['POST'])
@check_login_wrapper
def uncomplete_task_page(task_id):
    uncomplete_task(task_id)
    return render_template("task.html", task=get_task(task_id))

@app.route('/add_task',  methods = ['GET', 'POST'])
@check_login_wrapper
def add_task():
    if request.method == 'GET':
        return render_template("add_task.html", task_types=get_task_types(), units=UNITS)
    else:
        print(request.form)
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
        succeeded, msg = create_task(get_user(login_session["username"]), due_date, description, task_type_name, fields, reminders, reminder_datestrings)
        flash("Task added successfully!")
        return render_template("add_task.html", task_types=get_task_types())

@app.route('/search',  methods = ['GET', 'POST'])
@check_login_wrapper
def search():
    if request.method == 'GET':
        return render_template("tasks.html")
    else:

        search_text = request.form['search']
        print(search_text)
        # return render_template("search_result.html", tasks=search_descr(search_text))
        return render_template("tasks.html", tasks=search_descr(search_text), col_strings = ["Due Date"], col_vars = ["due_datestring"])
    # tokenize search texts, then return results sorted in order of number of matches
    # can make a more advanced search - only searching in description, task_type, patient_name entries, etc


# need to be able to filter and sort tasks on task page using javascript

    


if __name__ == '__main__':
    app.run(debug=True)
