import os
import re
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from bson.errors import InvalidId
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
        self.following = user_data.get('following', [])
        self.likes = user_data.get('likes', [])

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    except InvalidId:
        return None
    if user_data:
        return User(user_data)
    return None

# Helper function to handle like toggling
def toggle_like(trail_id, user):
    trail = trails_collection.find_one({"_id": ObjectId(trail_id)})
    if not trail:
        return

    if user.id in trail['likes']:
        trail['likes'].remove(user.id)
        user.likes.remove(trail_id)
    else:
        trail['likes'].append(user.id)
        user.likes.append(trail_id)
    
    users_collection.update_one({'_id': ObjectId(user.id)}, {"$set": {"likes": user.likes}})
    trails_collection.update_one({'_id': ObjectId(trail_id)}, {"$set": {"likes": trail['likes']}})


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please login to like trails.', 'error')
            return redirect(url_for('login'))

        liked = request.form.get('like')
        if liked:
            toggle_like(liked, current_user)
            return redirect(url_for('index'))
    query1 = request.args.get('q1')
    query2 = request.args.get('q2')
    # Get filter parameters
    filter_neighborhood = request.args.get('neighborhood')
    filter_difficulty = request.args.get('difficulty')
    filter_duration = request.args.get('duration')
    filter_following = request.args.get('following')

    mongo_query = {}

    # 1. Handle text search
    if query1:
        escaped_query = re.escape(query1)
        mongo_query["$or"] = [
            {"title": {"$regex": escaped_query, "$options": "i"}},
            {"neighborhood": {"$regex": escaped_query, "$options": "i"}}
        ]
    if query2:
        escaped_query = re.escape(query2)
        mongo_query["creator_username"] = {"$regex": escaped_query, "$options": "i"}
    
    # 2. Handle filters
    if filter_neighborhood:
        mongo_query['neighborhood'] = filter_neighborhood
    if filter_difficulty:
        mongo_query['difficulty'] = filter_difficulty
    if filter_duration:
        mongo_query['duration'] = filter_duration
    checked = False
    if filter_following and current_user.is_authenticated:
        mongo_query['created_by'] = {"$in": current_user.following}
        checked = True

    print(mongo_query)

    trails = list(trails_collection.find(mongo_query))

    # 3. Get all available filter options (for frontend dropdowns)
    neighborhoods = sorted(trails_collection.distinct('neighborhood'))
    difficulties = sorted(trails_collection.distinct('difficulty'))
    durations = sorted(trails_collection.distinct('duration'))

    return render_template(
        'index.html', 
        trails=trails, 
        query1=query1, 
        query2=query2, 
        neighborhoods=neighborhoods, 
        difficulties=difficulties, 
        durations=durations, 
        selected_neighborhood=filter_neighborhood, 
        selected_difficulty=filter_difficulty, 
        selected_duration=filter_duration, 
        checked=checked,
        datetime=datetime
    )

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
            'creator_username' : str(current_user.username),
            'created_at': datetime.now(timezone.utc),
            'comments' : [],
            'likes' : []
        }
        trails_collection.insert_one(trail_data)
        flash('Trail posted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('post_trail.html')

@app.route('/user/<user_id>', methods=['GET', 'POST'])
@login_required
def show_user(user_id):
    trails = list(trails_collection.find({"created_by" : user_id}))
    count = len(trails)
    current = current_user.id == user_id
    username = None
    if(ObjectId.is_valid(user_id)):
        username = users_collection.find_one({'_id': ObjectId(user_id)})["username"]
    following = next((x for x in current_user.following if x == user_id), None)
    followers = len(list(users_collection.find({'following' : {"$in": [user_id]} })))
    print(followers)
    if request.method == 'POST':
        if not following:
            current_user.following.append(user_id)
            users_collection.update_one({'_id': ObjectId(current_user.id)}, {"$set": {"following": current_user.following}})
            flash('Now following', 'success')
        else:
            current_user.following.remove(user_id)
            users_collection.update_one({'_id': ObjectId(current_user.id)}, {"$set": {"following": current_user.following}})
            flash('Unfollowed', 'success')
        return redirect(url_for('show_user', user_id=user_id))

    return render_template('user.html', username=username,trails=trails, count=count, current=current, following=following, followers=followers, user_id=user_id)

@app.route('/trail/info/<trail_id>', methods=['GET', 'POST'])
def trail_info(trail_id):
    try:
        trail = trails_collection.find_one({"_id" : ObjectId(trail_id)})
    except InvalidId:
        flash('Invalid trail ID.', 'error')
        return redirect(url_for('index'))

    if not trail:
        flash('Trail not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please login to comment or like.', 'error')
            return redirect(url_for('login'))
            
        liked = request.form.get('like')
        if liked:
            toggle_like(liked, current_user)
            return redirect(url_for('trail_info', trail_id=trail_id))
        comment = {str(current_user.username) : request.form.get('comment')}
        trail["comments"].append(comment)
        newComments = {'comments' : trail["comments"]}
        trails_collection.update_one({'_id': ObjectId(trail_id)}, {'$set': newComments})
        flash('Comment posted successfully!', 'success')
    return render_template('trail_info.html', trail=trail)

@app.route('/trail/<trail_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trail(trail_id):
    try:
        trail = trails_collection.find_one({'_id': ObjectId(trail_id)})
    except InvalidId:
        flash('Invalid trail ID.', 'error')
        return redirect(url_for('index'))
    
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
    try:
        oid = ObjectId(trail_id)
        trail = trails_collection.find_one({'_id': oid})
        if trail and trail.get('created_by') == current_user.id:
            trails_collection.delete_one({'_id': oid})
            flash('Trail deleted.', 'success')
    except InvalidId:
        flash('Invalid trail ID.', 'error')

    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
            
        if users_collection.find_one({'username': username}):
            flash('Username already exists', 'error')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            users_collection.insert_one({
                'username': username,
                'password': hashed_password,
                'following': [],
                'likes': []
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
