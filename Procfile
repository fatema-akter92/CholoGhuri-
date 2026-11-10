web: cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn chologhuri_project.wsgi:application --bind 0.0.0.0:$PORT
