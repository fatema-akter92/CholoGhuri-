@echo off
echo Starting CholoGhuri — Smart Bangladesh Tourism Guide...
cd /d "%~dp0backend"
python manage.py migrate
echo.
echo Open http://127.0.0.1:8000 in your browser!
echo Demo Traveler: traveler / CholoGhuri2026!
echo Demo Admin:    admin    / AdminCholo2026!
echo.
python manage.py runserver 127.0.0.1:8000
