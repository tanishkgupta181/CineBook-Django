# CineBook - Online Movie Booking and Management System

## Internship Final Project Report

---

# 1. Project Title

**CineBook - Online Movie Booking and Management System**

CineBook is a Django-based online movie booking and management platform inspired by modern movie ticket booking websites such as BookMyShow.

The system allows users to browse movies, search and discover movies, view movie details, check upcoming shows, select seats, make online payments, confirm bookings, view booking history, and download tickets.

The system also provides movie reviews and ratings, trailer and cast information, movie discovery APIs, and an administrator dashboard for monitoring bookings, revenue, movie performance, theater performance, payments, refunds, and user activity.

---

# 2. Project Objectives

The main objectives of CineBook are:

1. To develop a complete online movie ticket booking platform using Django.
2. To provide users with an easy movie discovery and booking experience.
3. To implement secure seat selection and temporary seat reservation.
4. To integrate online payments using Razorpay.
5. To generate booking tickets after successful payment.
6. To process ticket and email tasks using Celery and Redis.
7. To provide movie reviews and ratings.
8. To provide administrators with analytical reports and business insights.
9. To deploy the application on a cloud platform.
10. To provide a REST API for movie discovery.

---

# 3. Technology Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* Django Templates

## Backend

* Python
* Django 5.2.17
* Django REST Framework

## Database

### Local Development

* SQLite

### Production

* PostgreSQL
* Railway PostgreSQL service

## Payment Gateway

* Razorpay

## External API

* TMDB API
* Bearer-token based authentication

## Background Processing

* Celery
* Redis

## Web Server

* Gunicorn

## Deployment

* Railway

## Development and Version Control

* Visual Studio Code
* Git
* GitHub

---

# 4. Project Features

CineBook provides the following major features:

1. User registration
2. User login and logout
3. Movie listing
4. Movie search
5. Movie details
6. Genre and language information
7. Movie ratings
8. Movie reviews
9. Review editing
10. Review reporting
11. Trailer integration
12. Movie posters
13. Cast information
14. Similar movies
15. Trending movies
16. Recently released movies
17. Theater management
18. City information
19. Show date management
20. Show time management
21. Ticket price management
22. Seat selection
23. Live seat availability
24. Temporary seat reservation
25. Razorpay order creation
26. Razorpay payment verification
27. Payment failure handling
28. Payment cancellation handling
29. Payment retry
30. Duplicate booking protection
31. Payment amount verification
32. Booking confirmation
33. Booking history
34. Ticket PDF generation
35. Ticket download
36. Background ticket/email processing
37. Movie Discovery REST API
38. TMDB metadata integration
39. Admin dashboard
40. Revenue analytics
41. Booking analytics
42. Theater performance analysis
43. Movie performance analysis
44. Peak booking hour analysis
45. User growth statistics
46. Cancellation statistics
47. Refund statistics
48. Custom date filtering
49. CSV report export

---

# 5. User Module

The User Module allows customers to create accounts and securely access the CineBook system.

## User Functions

* User registration
* User login
* User logout
* Authentication
* Browse movies
* Search movies
* View movie details
* View available shows
* Select seats
* Make payments
* Confirm bookings
* View booking history
* Download tickets

Django's authentication framework is used for user authentication and access control.

---

# 6. Movie Management

The movie management system stores and displays detailed information about movies.

## Movie Information

Each movie can contain:

* Movie title
* Description
* Genre
* Language
* Duration
* Rating
* Release date
* Popularity
* Poster
* Trailer
* Age certification
* Cast members

The system supports multiple genres, languages, cast members, and movie posters through related models and many-to-many relationships.

---

# 7. Movie Discovery

CineBook provides movie discovery functionality for helping users find suitable movies.

Users can search or filter movies by:

* Movie title
* Genre
* Language
* City
* Theater
* Release date
* Rating
* Show timing

Movies can also be sorted using:

* Popularity
* Newest releases
* Rating
* Ticket price

The project also contains a Movie Discovery REST API implemented using Django REST Framework.

---

# 8. Movie Details and Recommendations

The movie details page displays:

* Movie title
* Description
* Genre
* Language
* Duration
* Rating
* Release information
* Posters
* Trailer
* Cast members
* Available upcoming shows
* Similar movies
* Trending movies
* Recently released movies
* Reviews and ratings

The system also records user movie activity for improving the overall discovery experience.

---

# 9. Reviews and Ratings

CineBook provides a review and rating system.

## Review Features

* 1 to 5 star rating
* Written reviews
* Review creation
* Review editing
* Review reporting
* Average rating calculation
* Watched-movie verification

A user can maintain one review for the same movie using an update-or-create operation.

Review access is restricted to users who have completed a booking for the corresponding movie.

---

# 10. Theater and Show Management

The system maintains theater and show information.

## Theater Information

* Theater name
* City

## Show Information

Each show contains:

* Movie
* Theater
* Show date
* Show time
* Ticket price
* Total seat capacity

Users can choose a suitable theater and show before continuing with seat selection.

---

# 11. Seat Booking System

The CineBook booking system provides seat-based movie booking.

The system stores:

* Customer name
* Email
* Phone number
* User
* Show
* Selected seats
* Number of seats
* Total booking amount
* Booking ID
* Payment reference
* Screen information
* Ticket information

The application validates seat selection before allowing a booking to continue.

---

# 12. Live Seat Availability

CineBook provides live seat availability for shows.

The system separates seats into:

* Booked seats
* Temporarily reserved seats
* Available seats
* Current user's reserved seats

This helps users see the current seat status before payment.

Database transactions and row-level locking are used in important booking operations to reduce conflicting seat selections.

---

# 13. Temporary Seat Reservation

CineBook provides temporary seat reservation during payment.

When a payment transaction is created, selected seats are temporarily associated with a pending `PaymentTransaction`.

The current reservation duration is:

**2 minutes**

The system stores:

* Reservation status
* Reservation expiry time
* Selected seats
* Show
* User
* Payment transaction

Expired reservations are automatically treated as unavailable only until their expiry time and are then released by the application logic.

This reduces the possibility of multiple customers attempting to purchase the same seats during the payment process.

---

# 14. Razorpay Payment Integration

Razorpay is integrated into CineBook for online payment processing.

## Payment Features

* Razorpay order creation
* Payment checkout
* Payment signature verification
* Payment amount verification
* Successful payment handling
* Failed payment handling
* Cancelled payment handling
* Payment retry
* Duplicate booking protection
* Payment transaction tracking
* Refund status tracking
* Razorpay webhook support

Payment information is stored in the `PaymentTransaction` model.

The system verifies the Razorpay payment signature before confirming a booking.

The booking amount is also compared with the Razorpay order amount before confirmation.

---

# 15. Payment Security

The payment module includes server-side validation.

Important security checks include:

* Razorpay credentials stored as environment variables
* Payment signature verification
* Payment order ownership verification
* Payment amount verification
* Payment transaction lookup
* Duplicate booking protection
* Seat conflict checking
* Temporary reservation validation

Production payment secrets are not stored directly in source code.

---

# 16. Booking Confirmation

After successful payment verification, CineBook creates a booking record containing:

* Booking ID
* User
* Movie
* Theater
* Show
* Seats
* Customer information
* Total amount
* Payment reference
* Screen

The confirmed booking is then available from the user's booking history.

---

# 17. Ticket Management

After a successful booking, CineBook generates a ticket containing important booking information.

The ticket can contain:

* Customer name
* Movie name
* Theater name
* Screen
* Show date
* Show time
* Selected seats
* Booking ID
* Payment reference
* Total amount

Users can download the generated ticket as a PDF.

---

# 18. Background Task Processing

Celery and Redis are used for background task processing.

The project contains the background task:

```text
movies.tasks.generate_ticket_and_send_email
```

This task is used for operations such as ticket generation and email processing after successful bookings.

Redis acts as the broker/result backend and Celery processes queued background tasks.

In the production Railway environment, the Django web server and Celery worker are started together using the project startup script:

```bash
python start.py
```

---

# 19. TMDB Integration

CineBook supports TMDB API integration for movie metadata.

TMDB can provide information such as:

* Movie information
* Posters
* Cast
* Popularity
* Release information
* Additional movie metadata

The application uses Bearer-token authentication for TMDB API requests.

The TMDB token is configured through an environment variable and is not stored in the source code.

---

# 20. Movie Discovery API

CineBook provides a REST API using Django REST Framework.

The movie discovery endpoint is:

```text
/api/movies/
```

The API can provide movie information including:

* ID
* Title
* Description
* Genre
* Language
* Duration
* Rating
* Average rating
* Trailer URL
* Age certification
* Poster URL
* Release date
* Popularity

Filtering is supported for movie discovery parameters such as search, genre, and language.

---

# 21. Admin Dashboard

CineBook provides a dedicated Admin Dashboard for monitoring business operations.

The dashboard is designed for authorized administrators.

It provides analytics for:

* Revenue
* Bookings
* Seats booked
* Movie performance
* Theater performance
* Theater occupancy
* Peak booking hours
* Payment statistics
* Cancellation statistics
* Refund statistics
* User growth

---

# 22. Revenue Analytics

The Admin Dashboard provides revenue information for selected periods.

Revenue can be analyzed by:

* Day
* Week
* Month
* Year

The dashboard uses Django ORM aggregation to calculate revenue based on booking records.

---

# 23. Booking Trends

Booking trends are displayed based on booking date.

Each record can contain:

* Booking date
* Number of bookings
* Seats booked
* Revenue

This allows administrators to analyze changes in customer booking activity.

---

# 24. Theater Performance and Occupancy

The Admin Dashboard provides theater-wise performance information.

It can display:

* Theater name
* City
* Theater capacity
* Booked seats
* Occupancy
* Number of bookings
* Revenue

Occupancy is calculated using booking and show information for the selected date range.

---

# 25. Most Booked Movies

The dashboard identifies movies with higher booking activity.

The report includes:

* Movie name
* Number of bookings
* Seats booked
* Revenue

This helps administrators identify popular movies.

---

# 26. Peak Booking Hours

The dashboard analyzes booking and show activity by hour.

Information includes:

* Hour
* Number of bookings
* Seats booked
* Revenue

This can be used to identify periods with higher booking activity.

---

# 27. Cancellation and Refund Statistics

The Admin Dashboard provides payment and cancellation information.

It can include:

* Total payment attempts
* Successful payments
* Failed payments
* Cancelled payments
* Cancellation rate
* Refund status
* Completed refunds
* Refund amount
* Pending refunds

This helps administrators monitor payment performance.

---

# 28. User Growth

User registration activity can be analyzed by date.

The report displays:

* Registration date
* Number of newly registered users

This helps administrators understand user growth.

---

# 29. Custom Date Range Filtering

The Admin Dashboard supports custom date-range filtering.

Administrators can select:

* From Date
* To Date

The selected date range is used for relevant analytics including:

* Revenue
* Bookings
* Seats
* Movie performance
* Theater performance
* Peak hours
* Payment statistics
* Refund statistics
* User growth

The dashboard uses database-level filtering and aggregation for these calculations.

---

# 30. CSV Export

The Admin Dashboard supports CSV report export.

The exported information can contain sections for:

* Summary
* Booking trends
* Movie performance
* Theater performance
* Peak booking hours
* Payment statistics
* Refund statistics
* User growth

CSV export allows administrators to save analytical information for offline processing.

---

# 31. Admin Authentication and Authorization

Sensitive dashboard information is protected using Django authentication and authorization mechanisms.

Dashboard access is restricted to authorized users according to the application's permission checks.

The system verifies authentication and administrator/staff access before displaying sensitive business analytics.

---

# 32. Database Design

The application uses Django models to manage:

* Movies
* Genres
* Languages
* Cast members
* Movie posters
* Theaters
* Shows
* Users
* Bookings
* User activity
* Reviews
* Review reports
* Payment transactions

---

# 33. Production Database

The production deployment uses **PostgreSQL on Railway**.

The current live database was successfully populated and verified with approximately:

```text
Movies:     49
Shows:      25,213
Theaters:   14
Genres:     16
Languages:  8
Cast:       323
```

The production database also contains booking and payment transaction records created during live testing.

---

# 34. Database Indexing

Database indexes have been implemented for frequently queried fields.

Important indexes include:

### Booking

* `booked_at`
* `(show, booked_at)`
* `(user, booked_at)`

### Show

* `(show_date, show_time)`
* `(theater, show_date)`
* `(movie, show_date)`

### PaymentTransaction

* `(show, status, expires_at)`
* `(status, created_at)`
* `(show, created_at)`
* `(refund_status, refunded_at)`

These indexes help improve filtering and reporting performance.

---

# 35. ORM Performance Optimization

The Admin Dashboard uses Django ORM aggregation rather than loading all records into Python.

Operations used include:

* `Count()`
* `Sum()`
* `Avg()`
* `Max()`
* `Coalesce()`
* `TruncDay()`
* `TruncWeek()`
* `TruncMonth()`
* `TruncYear()`
* `ExtractHour()`

Database-side aggregation reduces unnecessary application memory usage and allows analytical queries to be processed efficiently.

---

# 36. Large Dataset Scalability

The Admin Dashboard has been designed with scalable query patterns.

Performance considerations include:

1. Database indexing
2. Database-level aggregation
3. Date-based filtering
4. Composite indexes
5. Limited result retrieval
6. Avoiding unnecessary object loading
7. Efficient payment and booking filtering

These techniques provide a better foundation for larger booking datasets.

---

# 37. Security

CineBook includes multiple security measures:

* Django authentication
* Login-protected views
* Administrator authorization
* CSRF protection
* Server-side validation
* Payment signature verification
* Payment amount verification
* Duplicate booking protection
* Seat availability validation
* Temporary reservation validation
* Environment-based secret configuration

Production credentials such as Razorpay keys, TMDB tokens, database URLs, and Redis URLs are configured through environment variables.

No production secret is intended to be committed to GitHub.

---

# 38. Railway Deployment

CineBook is deployed on Railway.

## Production Components

```text
CineBook-Django
PostgreSQL
Redis
```

The application is connected to the GitHub repository and automatically deploys the production branch.

## Production Web Server

The application uses Gunicorn on the Railway Linux environment.

## Production Celery Worker

The Celery worker is started together with the Django application using:

```bash
python start.py
```

The startup script launches:

* Django/Gunicorn web server
* Celery worker

This setup was used because the Railway Free plan did not allow creation of another service.

---

# 39. Live Project

## Live Website

https://cinebook-django-production.up.railway.app/

## GitHub Repository

https://github.com/tanishkgupta181/CineBook-Django

---

# 40. Project Structure

```text
CineBook-Django/

├── admin_dashboard/
│
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
├── static/
│   ├── css/
│   └── images/
│
├── staticfiles/
│
├── templates/
│
├── media/
│
├── manage.py
├── start.py
├── requirements.txt
├── README.md
└── REPORT.md
```

---

# 41. Local Development

Create a virtual environment:

## Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## macOS/Linux

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Start Django:

```bash
python manage.py runserver
```

The local website can then be accessed at:

```text
http://127.0.0.1:8000/
```

---

# 42. Local Celery

For local background task processing:

```bash
python -m celery -A bookmyshow.celery:app worker --loglevel=info --pool=solo
```

Redis must be running locally for the Celery worker.

---

# 43. Environment Variables

The following environment variables are used by the project where required:

```text
SECRET_KEY
DEBUG
DATABASE_URL
TMDB_API_KEY
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
REDIS_URL
```

Production values are configured in Railway rather than stored in the GitHub repository.

---

# 44. Testing and Verification

The following Django checks were performed:

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

The final Django system check returned:

```text
System check identified no issues (0 silenced).
```

---

# 45. Production Booking Test

A complete live booking test was successfully performed.

The tested flow was:

```text
Movie Selection
      ↓
Show Selection
      ↓
Seat Selection
      ↓
Razorpay Order
      ↓
Payment
      ↓
Payment Verification
      ↓
Booking Confirmation
      ↓
Ticket Generation
      ↓
Ticket Download
```

The live booking test successfully confirmed:

* Movie booking
* Theater selection
* Screen selection
* Seat selection
* Razorpay payment
* Payment verification
* Booking creation
* Booking ID generation
* Payment reference generation
* Ticket PDF generation
* Ticket download

---

# 46. Production Payment Verification

The live payment integration was tested successfully with Razorpay.

The application successfully performed:

1. Razorpay order creation
2. Payment checkout
3. Payment verification
4. Payment transaction creation
5. Booking creation
6. Ticket generation
7. Ticket download

The production database was also verified for successful payment records.

---

# 47. Redis and Celery Verification

Redis connectivity was tested successfully in the Railway environment.

Celery was verified with:

```text
Connected to redis://...
celery@... ready.
```

The task:

```text
movies.tasks.generate_ticket_and_send_email
```

was successfully registered by the Celery application.

This confirms that the background processing infrastructure is configured for production.

---

# 48. Final Project Status

The CineBook Internship Final Project has successfully implemented the major movie booking, payment, ticketing, review, API, and administrative requirements.

The final implemented system includes:

```text
Django                         COMPLETED
PostgreSQL                     COMPLETED
Movie Management               COMPLETED
Movie Discovery                COMPLETED
Theater Management             COMPLETED
Show Management                COMPLETED
Seat Selection                 COMPLETED
Temporary Seat Reservation     COMPLETED
Razorpay Payment               COMPLETED
Payment Verification           COMPLETED
Booking System                 COMPLETED
Ticket Generation              COMPLETED
Ticket Download                COMPLETED
Redis                          COMPLETED
Celery                         COMPLETED
Reviews and Ratings            COMPLETED
Review Reporting               COMPLETED
Movie Discovery API            COMPLETED
Admin Dashboard                COMPLETED
Revenue Analytics              COMPLETED
Booking Analytics              COMPLETED
CSV Export                     COMPLETED
Railway Deployment             COMPLETED
```

---

# 49. Conclusion

CineBook successfully implements a complete online movie booking and management platform using Python and Django.

The system provides:

* Movie discovery
* Movie details
* Show management
* Theater management
* Seat selection
* Temporary reservations
* Razorpay payment
* Payment verification
* Booking confirmation
* Ticket generation
* Ticket download
* Reviews and ratings
* Movie discovery API
* Background processing
* Administrative analytics

The production deployment uses PostgreSQL for data storage, Redis for background task infrastructure, Celery for asynchronous processing, Razorpay for online payments, and Railway for cloud deployment.

The project was tested using Django system checks and a complete live movie booking flow, including successful payment and ticket download.

**CineBook - Internship Final Project: COMPLETED**
