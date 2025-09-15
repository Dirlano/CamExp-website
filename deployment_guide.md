Deployment Instructions (PythonAnywhere Free):
1. Sign up at pythonanywhere.com (free tier).
2. Create a new web app (Python 3.12, Django).
3. Upload the ZIP via Files tab, unzip.
4. Set virtualenv in Web tab.
5. Source virtualenv, pip install -r requirements.txt
6. Set WSGI file to camexp/wsgi.py
7. For ASGI/Channels: PythonAnywhere supports Daphne; configure in Web tab (manual config for free tier limited, use polling alternative if issues).
8. Set STATIC_ROOT and collectstatic.
9. Reload app.
10. Domain: yourusername.pythonanywhere.com
Note: Free tier has limitations on external APIs; test payments in sandbox.