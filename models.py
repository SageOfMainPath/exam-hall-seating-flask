# File-based data access functions for Admin, Student, Class, Room, Allotment
import os
from app import ADMIN_FILE, STUDENT_FILE, CLASS_FILE, ROOM_FILE, ALLOTMENT_FILE

def read_lines(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def write_lines(filepath, lines):
    with open(filepath, 'w') as f:
        for line in lines:
            f.write(line + '\n')

def append_line(filepath, line):
    with open(filepath, 'a') as f:
        f.write(line + '\n')

# Admin: username,password
# Student: id,name,roll_no,password,department
# Class: id,year,department,division
# Room: id,name
# Allotment: id,student_id,room_id

def get_admins():
    return [tuple(line.split(',')) for line in read_lines(ADMIN_FILE)]

def get_students():
    # Student: id,name,roll_no,password,department
    return [tuple(line.split(',')) for line in read_lines(STUDENT_FILE)]

def get_classes():
    return [tuple(line.split(',')) for line in read_lines(CLASS_FILE)]

def get_rooms():
    return [tuple(line.split(',')) for line in read_lines(ROOM_FILE)]

def get_allotments():
    return [tuple(line.split(',')) for line in read_lines(ALLOTMENT_FILE)]
