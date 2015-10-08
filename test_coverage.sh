coverage run --source='.' --omit=calendar_service/manage.py,calendar_service/wsgi.py  manage.py test
coverage report
