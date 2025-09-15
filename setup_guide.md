Installation Instructions:
1. Install Python 3.12.
2. Clone or unzip the project.
3. Create virtualenv: python -m venv venv
4. Activate: venv\Scripts\activate (Windows) or source venv/bin/activate (Unix)
5. pip install -r requirements.txt
6. python manage.py makemigrations
7. python manage.py migrate
8. python manage.py createsuperuser (for admin)
9. python manage.py runserver
10. Visit http://127.0.0.1:8000/
For geolocation: Add JS to send location to view for filtering.
For payments: Add API keys in settings.py, sign up at MTN/Orange developer portals.