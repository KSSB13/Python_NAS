import os
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
from werkzeug.utils import secure_filename

# --- App Initialization and Configuration ---
app = Flask(__name__)

# IMPORTANT: Change this secret key in a real application!
app.config["JWT_SECRET_KEY"] = "a-very-secure-and-long-secret-key-that-you-will-change"
# Configure the database file, which will be created inside a new 'instance' folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
# Set the location for file uploads
app.config["STORAGE_DIR"] = "data/files"


# --- Extensions Initialization ---
# Initialize the database extension
db = SQLAlchemy(app)
# Initialize the password hashing extension
bcrypt = Bcrypt(app)
# Initialize the JSON Web Token extension
jwt = JWTManager(app)


# --- Create Upload Directory ---
# Ensure the directory for storing files exists before the app starts
os.makedirs(app.config["STORAGE_DIR"], exist_ok=True)


# --- Database Model Definition ---
# This class defines the 'user' table in our database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # When creating a new user, automatically hash the password
    def __init__(self, username, password):
        self.username = username
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Method to check if a provided password is correct
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


# --- API Endpoint Definitions ---

# A simple "health check" to see if the server is running
@app.route("/api/health")
def health_check():
    return jsonify({"status": "ok"})

# --- User Management Endpoints ---

@app.route("/api/register", methods=["POST"])
def register():
    """Endpoint to register a new user."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": f"User '{username}' created successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    """Endpoint to log in a user and get an access token."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        # Create a token that identifies the user
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)

    return jsonify({"error": "Invalid username or password"}), 401


# --- File Management Endpoints ---
# All routes in this section are protected with @jwt_required()

@app.route("/api/files")
@jwt_required()
def list_files():
    """Lists all files in the storage directory."""
    storage_dir = app.config["STORAGE_DIR"]
    files_list = []
    for entry in os.scandir(storage_dir):
        info = entry.stat()
        files_list.append({"name": entry.name, "size": info.st_size})
    return jsonify(files_list)

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Handles file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['STORAGE_DIR'], filename))
        return jsonify({"message": f"File '{filename}' uploaded successfully"}), 201
    return jsonify({"error": "File upload failed"}), 500

@app.route('/api/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
    """Handles file downloads."""
    safe_filename = secure_filename(filename)
    try:
        return send_from_directory(
            app.config['STORAGE_DIR'], safe_filename, as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


# --- Main Execution Block ---
if __name__ == "__main__":
    # This context is needed for SQLAlchemy to know which app it's working with
    with app.app_context():
        # This command creates the database tables based on our User model
        db.create_all()
    # Start the Flask development server
    app.run(debug=True, port=8080)