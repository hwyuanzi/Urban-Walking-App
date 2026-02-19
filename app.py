import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/default_db")

client = MongoClient(mongo_uri)
db = client.get_default_database()

# TODO: Initialize trails collection here later
# e.g. trails_collection = db.trails
users_collection = db.users

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.role = user_data.get('role', 'tourist')

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None




@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def index_redirect():
    return redirect(url_for('index'))

# TODO: Add trail-related routes here (list trails, trail details, add trail, edit trail, delete trail, search trails)
# TODO: Password Authentication

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user_data = users_collection.find_one({'username': username})
        if user_data:
            user = User(user_data)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role') # tourist, hiker, moderator, poster
        if users_collection.find_one({'username': username}):
            flash('Username already exists')
        else:
            users_collection.insert_one({'username': username, 'role': role})
            flash('Registration successful')
            return redirect(url_for('login'))
        
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
