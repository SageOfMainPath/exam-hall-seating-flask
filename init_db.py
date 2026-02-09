from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    try:
        # Create all tables
        db.create_all()

        # Create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')  # Use environment variable
            admin = Admin(username='admin', password=generate_password_hash(default_password))
            db.session.add(admin)
            db.session.commit()
            logger.info('Default admin created.')
        else:
            logger.info('Default admin already exists.')

        logger.info('Database initialized successfully.')
    except Exception as e:
        logger.error(f'Error initializing the database: {e}')
