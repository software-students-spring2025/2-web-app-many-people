import os
from flask import Flask
from dotenv import load_dotenv
import pymongo
from flask_login import LoginManager
from bson.objectid import ObjectId

# Custom user class for Flask-Login
class User:
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.topic = user_data.get('topic')
        
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return self.id

def create_app():
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')
    
    # Add custom filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        if not text:
            return ""
        return text.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
    
    # Setup MongoDB connection
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("No MONGO_URI found in environment variables")
        
        client = pymongo.MongoClient(mongo_uri)
        # Verify connection
        client.admin.command('ping')
        print("MongoDB connection successful!")
        
        db_name = os.getenv("MONGO_DBNAME")
        db = client[db_name]
        
        # Ensure required collections exist
        required_collections = ['users', 'history', 'saved_translations']
        existing_collections = db.list_collection_names()
        
        for collection in required_collections:
            if collection not in existing_collections:
                db.create_collection(collection)
        
        app.db = db
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        app.db = None
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        if app.db is not None:
            user_data = app.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        return None
    
    # Register blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    
    return app 