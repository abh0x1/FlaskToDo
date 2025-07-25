from flask import Flask, request, render_template, flash, redirect, url_for, make_response, session
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = "abhishek1234"

db_name = "user.db"


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email)


def create_db():
    if not os.path.exists(db_name):
        conn = sqlite3.connect(db_name)
        conn.close()
        print(f"....... Database Created Successfully! :: {db_name} ........")
    else:
        print("......... Database Exists ..........")


def create_table():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "select name from sqlite_master where type='table' and name='users'")
        if cursor.fetchone() is None:
            print("........Table not found, creating table..........")

            cursor.execute(""" 
            create table users(
                           id integer primary key autoincrement,
                           name text not null,
                           email text unique not null,
                           city text not null 
                           )
                        """)
            conn.commit()

            print("..... Table Created :: users ...... ")
        else:
            print("....... Table Already Exists ..........")
    except sqlite3.Error as e:
        print(f"An error occurred {str(e)}")
        conn.rollback()
    finally:
        conn.close()


@app.route('/')
def home():
    if 'userId' in session:
        session.clear()
    return render_template('home.html')


@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == "POST":
        name = request.form.get('fname')
        email = request.form.get('email')

        if not name and not is_valid_email(email):
            flash("Both field should be required", "error")
            return redirect(url_for('login_user'))

        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute(
                "select * from users where name=? and email=?", (name, email))
            user = cursor.fetchone()

            if user:
                res = make_response(redirect(url_for('login_success')))
                res.set_cookie('userId', email)
                session['userId'] = email
                flash("Login successfully!", "success")
                return res
            else:
                flash("User not found!")
        except sqlite3.Error as e:
            flash(f"DB Error!{str(e)}", "error")
        finally:
            conn.close()
        return redirect(url_for('login_user'))
    return render_template('login.html')


@app.route('/login_success', methods=['GET', 'POST'])
def login_success():
    if 'userId' in session:
        user = session.get('userId')
        return render_template('login_success.html', user=user)
    else:
        flash("User Not Found!", "error")
        return redirect(url_for('home'))


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == "POST":
        name = request.form.get('fname')
        email = request.form.get('email')
        city = request.form.get('city')

        if not name or not email or not city:
            flash("All fields are required!", "error")
            return redirect(url_for('home'))

        if not is_valid_email(email):
            flash("Enter a valid email address!", "error")
            return redirect(url_for('home'))

        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute(
                "insert into users (name,email,city) values (?,?,?)", (name, email, city))
            conn.commit()

            res = make_response(redirect(url_for('home')))
            res.set_cookie('user_email', email)
            session['user_email'] = email
            flash("User added successfully!", "success")
            return res

        except sqlite3.IntegrityError:
            conn.rollback()
            flash("user email already exist", "error")
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Database error : {str(e)}", "error")
        finally:
            conn.close()

        return redirect(url_for('home'))
    return render_template('add.html')


@app.route('/search_user', methods=['GET', 'POST'])
def search_user():
    if request.method == "POST":
        email = request.form.get('email')

        if not email or not is_valid_email(email):
            flash("Enter a valid email", "error")
            return redirect(url_for('search_user'))

        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("select * from users where email=?", (email,))
            user = cursor.fetchone()

            if user:
                flash("user found", "success")
                return render_template('result.html', user=user)
            else:
                flash("User not found", "error")
                return redirect(url_for('search_user'))

        except sqlite3.Error as e:
            flash("Database error", "error")
        finally:
            conn.close()
    return render_template('search.html')


@app.route('/update_user', methods=['GET', 'POST'])
def update_user():
    if request.method == "POST":
        name = request.form.get('fname')
        email = request.form.get('email')
        city = request.form.get('city')

        if not email or not is_valid_email(email):
            flash("Correct Email required!", "error")
            return redirect(url_for('update_user'))

        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("select * from users where email=?", (email,))
            user = cursor.fetchone()

            if not user:
                flash("user not found!", "error")
                return redirect(url_for('update_user'))

            if not name:
                name = user[1]
            if not city:
                city = city[2]

            cursor.execute(
                'update users set name=?,city=? where email=?', (name, city, email))
            conn.commit()
            flash("user update successfully!", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash("db error!", "error")

        finally:
            conn.close()
        return redirect(url_for('update_user'))
    return render_template('update.html')


@app.route('/delete_user', methods=['POST', 'GET'])
def delete_user():
    if request.method == "POST":
        email = request.form.get('email')

        if not email and not is_valid_email(email):
            flash("Enter valid email!", "error")
            return redirect(url_for('delete_user'))

        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("delete from users where email=?", (email,))
            conn.commit()
            flash("User deleted successfully!", "success")
        except sqlite3.Error as e:
            flash("DB error!", "error")
            conn.rollback()
        finally:
            conn.close()
        return redirect(url_for('delete_user'))
    return render_template('delete.html')


@app.route('/all_user')
def all_user():
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('select * from users')
        rows = cursor.fetchall()
        return render_template('list.html', rows=rows)
    except sqlite3.Error as e:
        flash("db error!", "error")
        conn.rollback()
        return redirect(url_for('home'))
    finally:
        conn.close()


if __name__ == "__main__":
    create_db()
    create_table()
    app.run(debug=True, port=8080)
