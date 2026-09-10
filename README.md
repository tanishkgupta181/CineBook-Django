# CineBook - BookMyShow Style Django Project

A student-friendly movie ticket booking website built with Python and Django.

## Features
- Home page with movie cards
- Movie details page
- Search movies
- Show timings
- Simple ticket booking form
- Booking confirmation page
- Django admin for adding movies and shows
- SQLite database
- Responsive CSS

## Run locally

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

Admin: http://127.0.0.1:8000/admin/

## Demo data
After migrations, run:
```bash
python manage.py seed_demo
```

## Project structure
- `bookmyshow/` - Django project settings
- `movies/` - main application
- `templates/` - HTML templates
- `static/` - CSS and JavaScript
- `media/` - uploaded movie posters

## Deployment
For a live URL, deploy this project to a Django-compatible hosting provider and set `DEBUG=False`, `ALLOWED_HOSTS`, static files, and a production database as required by the provider.
