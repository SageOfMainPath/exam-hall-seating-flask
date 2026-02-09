from flask import render_template, redirect, url_for, flash, request, session
from app import app
from models import get_admins, get_students, get_classes, get_rooms, get_allotments, ADMIN_FILE, STUDENT_FILE, CLASS_FILE, ALLOTMENT_FILE, append_line, write_lines
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed = hash_password(password)
        # Admin login
        for admin in get_admins():
            if admin[0] == username and admin[1] == hashed:
                session['user'] = username
                session['role'] = 'admin'
                return redirect(url_for('admin_dashboard'))
        # Student login
        for student in get_students():
            if student[1] == username and student[3] == hashed:
                session['user'] = student[0]
                session['role'] = 'student'
                return redirect(url_for('student_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        from routes import hash_password
        hashed = hash_password(password)
        for admin in get_admins():
            if admin[0] == username and admin[1] == hashed:
                session['user'] = username
                session['role'] = 'admin'
                return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    classes = get_classes()
    students = get_students()
    return render_template('admin_dashboard.html', classes=classes, students=students)

@app.route('/admin/class/add', methods=['POST'])
def add_class():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    year = request.form.get('year')
    department = request.form.get('department')
    division = request.form.get('division')
    class_id = str(len(get_classes())+1)
    # Only add if all fields are provided
    if not (year and department and division):
        flash('All fields are required to add a class.', 'danger')
        return redirect(url_for('admin_dashboard'))
    append_line(CLASS_FILE, f"{class_id},{year},{department},{division}")
    flash('Class added successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/class/delete/<class_id>')
def delete_class(class_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    classes = get_classes()
    classes = [c for c in classes if c[0] != class_id]
    write_lines(CLASS_FILE, [','.join(c) for c in classes])
    flash('Class deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/student/add', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    password = hash_password(request.form.get('password'))
    department = request.form.get('department')
    student_id = str(len(get_students())+1)
    append_line(STUDENT_FILE, f"{student_id},{name},{roll_no},{password},{department}")
    flash('Student added successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/student/delete/<student_id>')
def delete_student(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    students = get_students()
    students = [s for s in students if s[0] != student_id]
    write_lines(STUDENT_FILE, [','.join(s) for s in students])
    flash('Student deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/allotment/delete/<allotment_id>')
def delete_allotment(allotment_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    allotments = get_allotments()
    allotments = [a for a in allotments if a[0] != allotment_id]
    write_lines(ALLOTMENT_FILE, [','.join(a) for a in allotments])
    flash('Allotment deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    student_id = session.get('user')
    allotments = [a for a in get_allotments() if a[1] == student_id]
    return render_template('student_dashboard.html', allotments=allotments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        password = request.form.get('password')
        if not (name and roll_no and password):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        # Check for duplicate roll_no
        for s in get_students():
            if s[2] == roll_no:
                flash('Student with this Roll No. already exists.', 'danger')
                return render_template('register.html')
        student_id = str(len(get_students())+1)
        from routes import hash_password
        append_line(STUDENT_FILE, f"{student_id},{name},{roll_no},{hash_password(password)},")
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin/auto_seat', methods=['POST'])
def auto_seat():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    num_students = int(request.form.get('num_students'))
    total_seats = int(request.form.get('total_seats'))
    # Get all students, up to num_students
    all_students = get_students()[:num_students]
    from random import shuffle
    shuffle(all_students)
    # Make the grid as square as possible
    import math
    n = min(total_seats, len(all_students))
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    seat_grid = [[None for _ in range(cols)] for _ in range(rows)]
    placed = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break
            # Try to avoid placing same dept adjacent
            candidate = None
            for s in all_students:
                if s in placed:
                    continue
                left = seat_grid[r][c-1][4] if c > 0 and seat_grid[r][c-1] else None
                up = seat_grid[r-1][c][4] if r > 0 and seat_grid[r-1][c] else None
                if (left is None or left != s[4]) and (up is None or up != s[4]):
                    candidate = s
                    break
            if not candidate:
                for s in all_students:
                    if s not in placed:
                        candidate = s
                        break
            seat_grid[r][c] = candidate
            placed.append(candidate)
            idx += 1
    return render_template('seat_plan.html', seat_grid=seat_grid, cols=cols, total_seats=total_seats)
