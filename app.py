import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/sweproj2test")

client = MongoClient(mongo_uri)
db = client.get_database('glacier_gorillas')
trails_collection = db.trails

bcrypt = Bcrypt(app)

users_collection = db.users

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        # self.role = user_data['role']

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None



@app.route('/')
def index():
    trails = list(trails_collection.find())
    return render_template('index.html', trails=trails)

# TODO: Add trail-related routes here (edit trail, delete trail, search trails)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = users_collection.find_one({'username': username})

        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post_trail():
    if request.method == 'POST':
        trail_data = {
            'title': request.form.get('title'),
            'neighborhood': request.form.get('neighborhood'),
            'starting_point': request.form.get('starting_point'),
            'duration': request.form.get('duration'),
            'difficulty': request.form.get('difficulty'),
            'description': request.form.get('description')
        }
        trails_collection.insert_one(trail_data)
        return redirect(url_for('index'))
    return render_template('post_trail.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # role = request.form.get('role') # tourist, hiker, moderator, poster
        if users_collection.find_one({'username': username}):
            flash('Username already exists')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            users_collection.insert_one({
                'username': username,
                'password': hashed_password,
                # , 'role': role
            })
            flash('Registration successful')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
