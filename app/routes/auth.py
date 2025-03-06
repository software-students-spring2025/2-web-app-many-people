from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from bson.objectid import ObjectId
from app import User
import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user in database
        db = current_app.db
        if db is not None:
            user_data = db.users.find_one({'email': email})
            
            # Check if user exists and password is correct
            if not user_data or not check_password_hash(user_data['password'], password):
                flash('Please check your login details and try again.')
                return redirect(url_for('auth.login'))
                
            # Create user object and login
            user = User(user_data)
            login_user(user)
            
            # Set session variables
            session['user_id'] = str(user.id)
            
            # Update last login time
            db.users.update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {'last_login': datetime.datetime.now()}}
            )
            
            return redirect(url_for('main.lookup'))
        else:
            flash('Database connection error. Please try again later.')
            return redirect(url_for('auth.login'))
        
    return render_template('login.html')
    
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        topic = request.form.get('topic', '')
        
        # Form validation
        db = current_app.db
        if db is not None:
            # Check if email already exists
            user = db.users.find_one({'email': email})
            if user:
                flash('Email address already exists.')
                return redirect(url_for('auth.signup'))
                
            # Check if username is taken
            user = db.users.find_one({'username': username})
            if user:
                flash('Username is already taken.')
                return redirect(url_for('auth.signup'))
                
            # Check if passwords match
            if password != confirm_password:
                flash('Passwords do not match.')
                return redirect(url_for('auth.signup'))
                
            # Create new user
            new_user = {
                'username': username,
                'email': email,
                'password': generate_password_hash(password),
                'topic': topic,
                'created_at': datetime.datetime.now(),
                'last_login': datetime.datetime.now()
            }
            
            # Insert into database
            result = db.users.insert_one(new_user)
            
            # Create user object and login
            new_user['_id'] = result.inserted_id
            user = User(new_user)
            login_user(user)
            
            # Set session variables
            session['user_id'] = str(user.id)
            
            # Update last login time
            db.users.update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {'last_login': datetime.datetime.now()}}
            )
            
            flash('Account created successfully!')
            return redirect(url_for('main.lookup'))
        else:
            flash('Database connection error. Please try again later.')
            return redirect(url_for('auth.signup'))
        
    return render_template('signup.html')
    
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 