from flask import render_template, redirect, url_for, flash, request, session
from app import app
from models import (
    get_admins, get_students, get_classes, get_rooms, get_allotments,
    ADMIN_FILE, STUDENT_FILE, CLASS_FILE, ALLOTMENT_FILE,
    append_line, write_lines
)
import hashlib
from types import SimpleNamespace
from random import shuffle


def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode()).hexdigest()


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
            if len(admin) >= 2 and admin[0] == username and admin[1] == hashed:
                session['user'] = username
                session['role'] = 'admin'
                return redirect(url_for('admin_dashboard'))

        # Student login:
        # username = student name (index 1)
        # password = roll_no (auto-set), hashed and stored in index 3
        for student in get_students():
            if len(student) >= 4 and student[1] == username and student[3] == hashed:
                session['user'] = student[0]  # student_id
                session['role'] = 'student'
                return redirect(url_for('student_dashboard'))

        flash('Invalid credentials', 'danger')

    return render_template('login.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed = hash_password(password)

        for admin in get_admins():
            if len(admin) >= 2 and admin[0] == username and admin[1] == hashed:
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

    classes = [
        SimpleNamespace(id=c[0], year=c[1], department=c[2], division=c[3])
        for c in get_classes()
        if len(c) >= 4
    ]

    # Students as tuples for template indexing:
    # student row format: id,name,roll,password,year,department,division
    students = []
    for s in get_students():
        s = list(s)
        while len(s) < 7:
            s.append("")
        students.append(tuple(s))

    allotments = get_allotments()

    return render_template(
        'admin_dashboard.html',
        classes=classes,
        students=students,
        allotments=allotments
    )


@app.route('/admin/class/add', methods=['POST'])
def add_class():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    year = request.form.get('year')
    department = request.form.get('department')
    division = request.form.get('division')

    if not (year and department and division):
        flash('All fields are required to add a class.', 'danger')
        return redirect(url_for('admin_dashboard'))

    class_id = str(len(get_classes()) + 1)
    append_line(CLASS_FILE, f"{class_id},{year},{department},{division}")
    flash('Class added successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/class/delete/<class_id>')
def delete_class(class_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    classes = get_classes()
    classes = [c for c in classes if len(c) > 0 and c[0] != class_id]
    write_lines(CLASS_FILE, [','.join(c) for c in classes])
    flash('Class deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/student/add', methods=['POST'])
def add_student():
    """
    Password box removed from UI.
    Auto password = roll_no (hashed).
    Saves year + department + division(section).
    """
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    year = request.form.get('year')
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    department = request.form.get('department', '')
    division = request.form.get('division', '')

    if not (year and name and roll_no and department and division):
        flash('Year, Name, Roll No, Department, and Section are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    student_id = str(len(get_students()) + 1)

    # Auto password = roll_no
    password_hash = hash_password(roll_no)

    # Save format: id,name,roll_no,password,year,department,division
    append_line(STUDENT_FILE, f"{student_id},{name},{roll_no},{password_hash},{year},{department},{division}")

    flash(f"Student added successfully. Password is Roll No: {roll_no}", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/student/delete/<student_id>')
def delete_student(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    students = get_students()
    students = [s for s in students if len(s) > 0 and s[0] != student_id]
    write_lines(STUDENT_FILE, [','.join(s) for s in students])
    flash('Student deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/allotment/delete/<allotment_id>')
def delete_allotment(allotment_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    allotments = get_allotments()
    allotments = [a for a in allotments if len(a) > 0 and a[0] != allotment_id]
    write_lines(ALLOTMENT_FILE, [','.join(a) for a in allotments])
    flash('Allotment deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student_id = session.get('user')
    allotments = [a for a in get_allotments() if len(a) > 1 and a[1] == student_id]
    return render_template('student_dashboard.html', allotments=allotments)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Keep registration as-is.
    If your register.html does not include year/division, it's okay.
    We will pad missing fields when reading.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        password = request.form.get('password')
        department = request.form.get('department', '')

        if not (name and roll_no and password):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        for s in get_students():
            if len(s) > 2 and s[2] == roll_no:
                flash('Student with this Roll No. already exists.', 'danger')
                return render_template('register.html')

        student_id = str(len(get_students()) + 1)

        # This saves only 5 fields, older format.
        # That's okay because admin_dashboard() pads to 7.
        append_line(STUDENT_FILE, f"{student_id},{name},{roll_no},{hash_password(password)},{department}")

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# -------------------------------
# BETTER SEATING PLAN (auto_seat)
# -------------------------------
@app.route('/admin/auto_seat', methods=['POST'])
def auto_seat():
    """
    Seating improvements:
    - Round-robin across departments
    - Checkerboard seat fill
    - Min-conflict selection per seat
    """
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    num_students = int(request.form.get('num_students') or 0)
    total_seats = int(request.form.get('total_seats') or 0)

    raw_students = get_students()[:num_students]

    # Normalize to 7 fields: id,name,roll,password,year,department,division
    students = []
    for s in raw_students:
        s = list(s)
        while len(s) < 7:
            s.append("")
        students.append(tuple(s))

    if total_seats <= 0 or len(students) == 0:
        flash("Please provide valid numbers for students and seats.", "danger")
        return redirect(url_for('admin_dashboard'))

    import math
    n = min(total_seats, len(students))
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    seat_grid = [[None for _ in range(cols)] for _ in range(rows)]

    def seat_positions_checkerboard(r_count, c_count, max_n):
        even, odd = [], []
        for r in range(r_count):
            for c in range(c_count):
                (even if (r + c) % 2 == 0 else odd).append((r, c))
        return (even + odd)[:max_n]

    seat_positions = seat_positions_checkerboard(rows, cols, n)

    def dept_of(stu):
        # department is index 5 in new format
        return (stu[5] or "").strip() or "UNKNOWN"

    def conflict_score(candidate_student, r, c):
        cand_dept = dept_of(candidate_student)
        score = 0

        # N/S/E/W neighbors
        for rr, cc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
            if 0 <= rr < rows and 0 <= cc < cols:
                other = seat_grid[rr][cc]
                if other and dept_of(other) == cand_dept:
                    score += 10

        # diagonals
        for rr, cc in [(r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)]:
            if 0 <= rr < rows and 0 <= cc < cols:
                other = seat_grid[rr][cc]
                if other and dept_of(other) == cand_dept:
                    score += 4

        return score

    # Group by department and shuffle
    dept_groups = {}
    for s in students[:n]:
        d = dept_of(s)
        dept_groups.setdefault(d, []).append(s)

    for d in dept_groups:
        shuffle(dept_groups[d])

    dept_keys = list(dept_groups.keys())
    shuffle(dept_keys)

    rr_list = []
    i = 0
    while len(rr_list) < n:
        d = dept_keys[i % len(dept_keys)]
        if dept_groups[d]:
            rr_list.append(dept_groups[d].pop())
        i += 1

    remaining = rr_list[:]

    for (r, c) in seat_positions:
        if not remaining:
            break

        best_idx = 0
        best_sc = None
        for idx, stu in enumerate(remaining):
            sc = conflict_score(stu, r, c)
            if best_sc is None or sc < best_sc:
                best_sc = sc
                best_idx = idx
                if best_sc == 0:
                    break

        seat_grid[r][c] = remaining.pop(best_idx)

    return render_template('seat_plan.html', seat_grid=seat_grid, cols=cols, total_seats=total_seats)
