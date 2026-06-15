# from core.config.secret import Secrets

# print(Secrets.APP_ENV)
# print(Secrets.DATABASE_HOST)


import logging
import sys

# from core.config.settings import settings

# print(settings.project_root)

# print(settings.database_url)

# print(settings.raw_data_dir)
# def test_db_connection():
#     """ Test the database connection by executing a simple query to verify connectivity and proper configuration.
#     """
# if __name__ != "__main__":
#     try:
#         initialize_system()
#     except InitializationError as e:
#         logger.critical(f"Auto-initialization failed: {e}")
#         sys.exit(1)

#     with db_manager.session_scope() as session:
#         try:
#             result = session.execute(text("SELECT 1"))
#             print("Database connection successful:", result.scalar())
#         except Exception as e:
#             print("Database connection failed:", str(e))

# test_db_connection()
# db = db_manager.check_connection()

# print(db)



from core.config.startup.initialize import InitializationError, initialize_system ,initializer
logger = logging.getLogger(__name__)

# test_initialize_system()
def test_initialize_system():
    """ Test the system initialization process to ensure that all components are set up correctly without errors.
    """
    try:
        initialize_system()
        print("System initialization successful.")

        print("Initialization checks passed.")

    except InitializationError as e:
        print(f"System initialization failed: {e}")
test_initialize_system()
