web: gunicorn euphrosyne.wsgi -b 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:=3} --max-requests 100 --timeout 60
postdeploy: python manage.py migrate 
