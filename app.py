import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
from db import trails_collection, users_collection

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None



@app.route('/')
def index():
    query = request.args.get('q')
    if query:
        # Case-insensitive search for title or neighborhood
        trails = list(trails_collection.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"neighborhood": {"$regex": query, "$options": "i"}}
            ]
        }))
    else:
        trails = list(trails_collection.find())
    return render_template('index.html', trails=trails, query=query)

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
            flash('Invalid username or password', 'error')
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
            'description': request.form.get('description'),
            'created_by': str(current_user.id),
            'created_at': datetime.utcnow()
        }
        trails_collection.insert_one(trail_data)
        flash('Trail posted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('post_trail.html')

@app.route('/trail/<trail_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trail(trail_id):
    trail = trails_collection.find_one({'_id': ObjectId(trail_id)})
    
    if not trail:
        flash('Trail not found.', 'error')
        return redirect(url_for('index'))
    
    # Check ownership
    if trail.get('created_by') != current_user.id:
        flash('You do not have permission to edit this trail.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        updated_data = {
            'title': request.form.get('title'),
            'neighborhood': request.form.get('neighborhood'),
            'starting_point': request.form.get('starting_point'),
            'duration': request.form.get('duration'),
            'difficulty': request.form.get('difficulty'),
            'description': request.form.get('description')
        }
        trails_collection.update_one({'_id': ObjectId(trail_id)}, {'$set': updated_data})
        flash('Trail updated successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_trail.html', trail=trail)

@app.route('/trail/<trail_id>/delete', methods=['POST'])
@login_required
def delete_trail(trail_id):
    trail = trails_collection.find_one({'_id': ObjectId(trail_id)})
    if trail and trail.get('created_by') == current_user.id:
        trails_collection.delete_one({'_id': ObjectId(trail_id)})
        flash('Trail deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if users_collection.find_one({'username': username}):
            flash('Username already exists', 'error')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            users_collection.insert_one({
                'username': username,
                'password': hashed_password,
            })
            flash('Registration successful', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
