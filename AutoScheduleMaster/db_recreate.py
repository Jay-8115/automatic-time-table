from app import app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    """Drop all tables and recreate them."""
    logger.info("Dropping all tables...")
    with app.app_context():
        db.drop_all()
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("Database schema recreated successfully!")

if __name__ == "__main__":
    recreate_database()