#!/usr/bin/env python
"""
Vercel build script for Django
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Output: {result.stdout}")
    return True

def main():
    """Main build function"""
    # Change to project directory
    project_dir = Path(__file__).parent / 'scr'
    os.chdir(project_dir)
    
    # Set Django settings for Vercel
    os.environ['DJANGO_SETTINGS_MODULE'] = 'base.settings_vercel'
    
    # Run Django commands
    commands = [
        'python manage.py collectstatic --noinput',
        'python manage.py migrate --run-syncdb',
    ]
    
    for command in commands:
        if not run_command(command):
            sys.exit(1)
    
    print("Build completed successfully!")

if __name__ == '__main__':
    main()