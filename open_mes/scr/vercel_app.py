"""
Vercel deployment WSGI application
"""
import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings module for Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings_vercel')

try:
    # Import Django setup
    import django
    from django.conf import settings
    
    # Setup Django
    django.setup()
    
    # Check if database exists and run migrations if needed
    from django.core.management import execute_from_command_line
    from django.db import connection
    from django.db.utils import OperationalError
    
    def ensure_database_ready():
        """Ensure database is ready by running migrations if needed"""
        try:
            # Test database connection (SQL Server compatible)
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            print("Database connection successful")
        except Exception as db_error:
            # Database connection failed or needs migration
            print(f"Database not ready: {db_error}")
            print("Running migrations...")
            try:
                # Run migrations programmatically
                from django.core.management import call_command
                call_command('migrate', verbosity=1, interactive=False)
                print("Migrations completed successfully")
            except Exception as e:
                print(f"Migration failed: {e}")
                # Continue with the app anyway
    
    # Ensure database is ready
    ensure_database_ready()
    
    # Import Django WSGI application
    from django.core.wsgi import get_wsgi_application
    
    # Create WSGI application
    app = get_wsgi_application()
    
except Exception as e:
    # Fallback error handler for debugging
    def app(environ, start_response):
        response_body = f'Error initializing Django: {str(e)}'.encode('utf-8')
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/plain'),
                          ('Content-Length', str(len(response_body)))]
        start_response(status, response_headers)
        return [response_body]