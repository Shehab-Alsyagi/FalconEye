# from core.config.secret import Secrets

# print(Secrets.APP_ENV)
# print(Secrets.DATABASE_HOST)


from core.config.settings import settings

# print(settings.project_root)

print(settings.database_url)

# print(settings.raw_data_dir)


from sqlalchemy import text

from core.database.connection import (db_manager)

def test_db_connection():
    """ Test the database connection by executing a simple query to verify connectivity and proper configuration.
    """
    with db_manager.session_scope() as session:
        try:
            result = session.execute(text("SELECT 1"))
            print("Database connection successful:", result.scalar())
        except Exception as e:
            print("Database connection failed:", str(e))

test_db_connection()
db = db_manager.check_connection()

print(db)
