# login.py
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Blueprint, Flask, render_template, redirect, url_for, request
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash



login_blueprint = Blueprint('login', __name__)
login_manager = LoginManager()

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    user = User()
    user.id = username
    return user

@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # validate username and password
        conn = sqlite3.connect('kTunes.sqlite')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user:
            stored_hash = user[2 ]
            if check_password_hash(stored_hash, password):
                user_obj = User()
                user_obj.id = username
                login_user(user_obj)
                return redirect(url_for('ktunes.playlist'))
            else:
                error = "Invalid password"
                print("Debug: Invalid username or password", user, check_password_hash(stored_hash, password))
        else:
            error = "User does not exist"
  
    return render_template('login.html', error=error)


@login_blueprint.route('/register', methods=['GET', 'POST'])
def register(): 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('kTunes.sqlite')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
        conn.commit()
        conn.close()

        return redirect(url_for('login.login'))
    return render_template('register.html')


@login_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out'