#!/bin/bash

python manage.py compilemessages
gunicorn euphrosyne.wsgi -b 0.0.0.0:$PORT --max-requests 100 --timeout 60 --log-file -