from database import *
from flask import Flask, request, redirect, render_template, Response, send_file, url_for, flash
from flask import session as login_session
import json
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = "a;lfkdsjaflksdj"

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
    return render_template("dashboard.html", task_types = get_task_types())

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
    required_fields = []
    optional_fields = []
    for field in request.form:
        if field in ["task_type"] or "required" in field or request.form[field] == "":
            continue
        else:
            count = field.split("_")[1]
            if "required_"+count in request.form:
                required_fields.append(request.form[field])
            else:
                optional_fields.append(request.form[field])
    create_task_type(task_type, required_fields, optional_fields)
    flash("Task Type: " + task_type + " created!")

    return redirect(url_for('dashboard'))

@app.route('/tasks')
@check_login_wrapper
def tasks():
    return render_template("tasks.html", tasks=get_tasks(), col_strings = ["Due Date"], col_vars = ["due_datestring"])

@app.route('/task/<int:task_id>')
@check_login_wrapper
def task(task_id):
    return render_template("task.html", task=get_task(task_id))

@app.route('/add_task',  methods = ['GET', 'POST'])
@check_login_wrapper
def add_task():
    if request.method == 'GET':
        return render_template("add_task.html", task_types=get_task_types())
    else:
        print(request.form)
        task_type_name = request.form['task_type']
        task_type = get_task_type_by_name(task_type_name)
        due_date_str = request.form["due_date"]
        due_date = datetime. strptime(due_date_str, '%Y-%m-%d')
        description = request.form["description"]
        fields = {}
        for field in request.form:
            if field not in ["task_type", "due_date", "description"]: # TODO - don't let the use make custom fields using these names
                fields[field] = request.form[field]
        succeeded, msg = create_task(get_user(login_session["username"]), due_date, description, task_type_name, fields)
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