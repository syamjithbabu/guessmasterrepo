#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys



def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guessmaster.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()



# def create_admin_user():
#     username = 'admin'  # Set your desired admin username here
#     password = '1234'  # Set your desired admin password here

#     if not User.objects.filter(username=username).exists():
#         User.objects.create_superuser(username=username, password=password)

# create_admin_user()

