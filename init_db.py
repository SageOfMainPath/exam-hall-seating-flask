from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
    print('Database initialized and default admin created.')
