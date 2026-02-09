from flask import Flask
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# File paths for data storage
DATA_DIR = 'data'
ADMIN_FILE = os.path.join(DATA_DIR, 'admins.txt')
STUDENT_FILE = os.path.join(DATA_DIR, 'students.txt')
CLASS_FILE = os.path.join(DATA_DIR, 'classes.txt')
ROOM_FILE = os.path.join(DATA_DIR, 'rooms.txt')
ALLOTMENT_FILE = os.path.join(DATA_DIR, 'allotments.txt')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

from routes import *

if __name__ == '__main__':
    app.run(debug=True)
