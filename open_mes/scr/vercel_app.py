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