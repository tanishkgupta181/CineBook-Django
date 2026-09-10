   # CineBook – BookMyShow Style Django Movie Booking Platform

CineBook is a full-stack movie ticket booking web application built with **Python, Django, PostgreSQL, Razorpay, Redis, and Celery**. It provides a BookMyShow-style experience for discovering movies, viewing show timings, selecting seats, making online payments, and downloading booking tickets.

## Live Project

**Live Website:**
https://cinebook-django-production.up.railway.app/

**GitHub Repository:**
https://github.com/tanishkgupta181/CineBook-Django

## Features

### Movie Discovery

* Movie listing with posters and details
* Movie search
* Genre and language based filtering
* Movie ratings and reviews
* Movie trailers
* Cast information
* Similar and trending movies
* Recently released movies
* Movie Discovery REST API

### Show & Theater Management

* Multiple theaters
* Multiple movie shows
* Show date and time selection
* Ticket price management
* Live seat availability
* Temporary seat reservation during payment

### Booking System

* User registration and login
* Seat selection
* Duplicate seat protection
* Booking confirmation
* Booking history
* Booking details
* Ticket PDF download

### Online Payment

* Razorpay payment gateway integration
* Razorpay order creation
* Secure payment signature verification
* Payment amount validation
* Payment transaction tracking
* Payment success, failed, and cancelled states
* Payment retry support

### Background Processing

* Redis for queue/backend
* Celery worker for background tasks
* Automatic ticket generation
* Email/ticket processing after successful booking

### Reviews & Moderation

* User reviews and ratings
* Review editing
* Review reporting
* Watched-movie based review access

### Admin Dashboard

* Movie management
* Theater management
* Show management
* Booking management
* Revenue and booking statistics
* Date-based filtering and reporting

## Technologies Used

| Technology            | Purpose                            |
| --------------------- | ---------------------------------- |
| Python                | Backend programming                |
| Django 5.2            | Web framework                      |
| Django REST Framework | REST API                           |
| PostgreSQL            | Production database                |
| SQLite                | Local development database         |
| Razorpay              | Online payment gateway             |
| Redis                 | Queue and result backend           |
| Celery                | Background task processing         |
| HTML5                 | Frontend structure                 |
| CSS3                  | Styling and responsive design      |
| JavaScript            | Interactive frontend functionality |
| Git & GitHub          | Version control                    |
| Railway               | Cloud deployment                   |

## Project Structure

```text
CineBook-Django/
│
├── admin_dashboard/
├── bookmyshow/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
│
├── movies/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py
│   ├── migrations/
│   └── management/
│
├── templates/
├── static/
├── staticfiles/
├── media/
├── manage.py
├── start.py
├── requirements.txt
├── README.md
└── REPORT.md
```

## Run Locally

Create and activate a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python manage.py migrate
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

## Environment Variables

Create a `.env` file for local development and configure the required variables.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=your-database-url

TMDB_API_KEY=your-tmdb-token

RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

REDIS_URL=redis://127.0.0.1:6379/0
```

**Never commit `.env` or production secrets to GitHub.**

## Celery

For local background task processing, start Redis and then run:

```bash
python -m celery -A bookmyshow.celery:app worker --loglevel=info --pool=solo
```

The project uses Celery for background ticket/email processing.

The production Railway deployment runs Django and the Celery worker together using:

```bash
python start.py
```

## Database

Local development can use SQLite, while the deployed production environment uses **PostgreSQL on Railway**.

The production database contains movie, show, theater, user, booking, review, and payment transaction data.

## Payment Flow

The payment workflow is:

```text
Select Movie
      ↓
Select Show
      ↓
Select Seats
      ↓
Create Razorpay Order
      ↓
Temporary Seat Reservation
      ↓
Razorpay Checkout
      ↓
Payment Verification
      ↓
Booking Confirmation
      ↓
Ticket Generation
      ↓
Ticket Download / Email
```

## Security & Validation

The application includes:

* Django authentication
* CSRF protection
* Login-protected booking and review operations
* Razorpay signature verification
* Payment amount verification
* Duplicate booking protection
* Seat availability validation
* Temporary payment reservations
* Environment-based secret configuration

## API

Movie discovery API:

```text
/api/movies/
```

The API supports movie discovery and filtering by available search parameters.

## Deployment

CineBook is deployed using **Railway**.

Production services include:

```text
CineBook-Django
PostgreSQL
Redis
```

The Django application uses Gunicorn in the Railway Linux environment and Celery for background processing.

Production environment variables are configured through Railway Variables.

## Testing Completed

The production deployment has been tested for:

* User login
* Movie details
* Show selection
* Seat selection
* Live seat availability
* Razorpay order creation
* Payment verification
* Booking confirmation
* Booking history
* Ticket PDF generation
* Ticket download
* Redis connection
* Celery worker startup
* Django system checks
* PostgreSQL production database

Django verification:

```bash
python manage.py check
```

Result:

```text
System check identified no issues (0 silenced).
```

## Project Report

Detailed project documentation is available in:

```text
REPORT.md
```

## Author

**Tanishk Gupta**

CineBook was developed as a Django internship/final project demonstrating movie discovery, ticket booking, online payment, database management, background task processing, and cloud deployment.
