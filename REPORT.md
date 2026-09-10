# CineBook – Movie Booking System

## Internship Final Project Report

---

## 1. Project Title

**CineBook – Online Movie Booking and Management System**

CineBook is a Django-based movie booking web application inspired by online movie ticket booking platforms. The system allows users to browse movies, view movie details, check available shows, select seats, make payments, manage bookings and download tickets.

The system also provides an administrator dashboard for monitoring business analytics and generating reports.

---

## 2. Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Django Templates

### Backend

* Python
* Django 5.2.17
* Django REST Framework

### Database

* SQLite

### Payment Gateway

* Razorpay

### External API

* TMDB API

### Background Processing

* Celery
* Redis

### Development Tools

* Visual Studio Code
* Git
* GitHub

---

## 3. Main Features

CineBook provides the following major features:

1. User registration and login
2. User authentication and logout
3. Movie listing
4. Movie search
5. Movie details
6. Movie genres and languages
7. Movie ratings
8. Movie reviews
9. Review reporting
10. Movie trailers
11. Movie posters
12. Cast information
13. Theater and city information
14. Show date and show time
15. Seat selection
16. Temporary seat reservation
17. Razorpay payment integration
18. Payment verification
19. Payment failure and cancellation handling
20. Booking confirmation
21. Booking history
22. Ticket generation
23. Ticket download
24. Email notification
25. Movie discovery API
26. TMDB movie metadata
27. Admin dashboard
28. Revenue analytics
29. Booking analytics
30. CSV report export

---

## 4. User Module

The user module allows customers to create an account and securely access the CineBook system.

### User Features

* Register account
* Login
* Logout
* Browse movies
* Search movies
* View movie information
* View available shows
* Select seats
* Make payment
* Receive booking confirmation
* View booking history
* Download ticket

Django's built-in authentication system is used for user login and authorization.

---

## 5. Movie Management

The movie management module stores and displays movie information.

Movie information includes:

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

The application also supports multiple genres, languages, cast members and movie posters.

---

## 6. Movie Discovery

CineBook provides movie discovery and filtering functionality.

Users can search and filter movies using information such as:

* Movie title
* Genre
* Language
* City
* Theater
* Release date
* Rating
* Show timing

Movies can also be sorted according to:

* Popularity
* Newest releases
* Rating
* Ticket price

The Movie Discovery API provides movie data using Django REST Framework.

---

## 7. Reviews and Ratings

Users can provide ratings and reviews for movies.

The review system includes:

* 1 to 5 star ratings
* Written reviews
* Review creation
* Review editing
* Review reporting
* Verified viewer checking
* Average movie rating calculation

A user can submit only one review for the same movie.

---

## 8. Theater and Show Management

The system stores theater and show information.

Each show contains:

* Movie
* Theater
* City
* Show date
* Show time
* Ticket price
* Available seat capacity

Users can select a suitable show before booking tickets.

---

## 9. Seat Booking System

The booking system allows users to select seats for a particular show.

The system stores:

* Customer information
* Selected seats
* Number of seats
* Show
* User
* Total booking amount
* Booking ID
* Payment reference
* Ticket information

The system prevents conflicting seat reservations during the booking process.

---

## 10. Temporary Seat Reservation

CineBook includes temporary seat reservation during the payment process.

When a payment transaction is created, selected seats can be temporarily reserved.

The reservation system stores an expiry time and automatically identifies expired pending reservations.

This reduces the possibility of multiple users attempting to book the same seats during payment.

---

## 11. Payment Integration

Razorpay is integrated into CineBook for online payments.

The payment system supports:

* Razorpay order creation
* Payment verification
* Successful payments
* Failed payments
* Cancelled payments
* Payment transaction tracking
* Payment retry
* Duplicate booking protection
* Amount verification
* Refund status tracking

Payment transactions are stored separately using the `PaymentTransaction` model.

---

## 12. Ticket Management

After a successful booking, CineBook generates a booking ticket.

The ticket contains relevant booking information such as:

* Customer name
* Movie
* Theater
* Show date
* Show time
* Selected seats
* Booking ID
* Payment information

Users can download their tickets from the booking system.

---

## 13. Background Task Processing

Celery and Redis are used for background processing.

Background processing is used for tasks such as ticket generation and email notification.

This prevents long-running operations from unnecessarily blocking the main web request.

---

## 14. TMDB Integration

The application supports TMDB API integration for movie metadata.

TMDB can provide information such as:

* Movie information
* Posters
* Backdrops
* Cast
* Trailer-related information
* Popularity
* Release information

Bearer-token authentication is used for API requests.

---

# 15. Admin Dashboard – Task 6

## Overview

CineBook provides a comprehensive Admin Dashboard for monitoring business performance.

The dashboard provides real-time analytical information including:

* Daily revenue
* Weekly revenue
* Monthly revenue
* Yearly revenue
* Booking trends
* Theater occupancy
* Most booked movies
* Top-performing theaters
* Peak booking hours
* Cancellation statistics
* Refund statistics
* User growth

---

## 16. Revenue Analytics

The Admin Dashboard provides revenue reports for:

### Daily Revenue

Displays revenue generated on the latest booking day within the selected date range.

### Weekly Revenue

Displays revenue grouped by week.

### Monthly Revenue

Displays revenue grouped by month.

### Yearly Revenue

Displays revenue grouped by year.

The revenue calculations are generated using Django ORM aggregation.

---

# 17. Booking Trends

The dashboard displays booking trends based on date.

Each trend contains:

* Booking date
* Number of bookings
* Seats booked
* Revenue

This allows administrators to identify changes in booking activity.

---

# 18. Theater Performance and Occupancy

The dashboard provides theater-wise performance information.

It displays:

* Theater name
* City
* Theater capacity
* Booked seats
* Average occupancy
* Number of bookings
* Revenue

Average occupancy is calculated across the booked show instances for the selected period.

---

# 19. Most Booked Movies

The dashboard identifies movies with the highest booking activity.

The report includes:

* Movie name
* Number of bookings
* Seats booked
* Revenue

This helps administrators identify popular movies.

---

# 20. Peak Booking Hours

The dashboard analyzes booking activity according to show time.

It displays:

* Hour
* Number of bookings
* Seats booked
* Revenue

This helps identify the most active booking/show periods.

---

# 21. Cancellation and Refund Statistics

The dashboard provides payment and cancellation information.

It includes:

* Total payment attempts
* Successful payments
* Failed payments
* Cancelled payments
* Cancellation rate
* Completed refunds
* Refund amount
* Pending refunds

This allows administrators to monitor payment performance and refund activity.

---

# 22. User Growth

The dashboard provides user registration growth based on date.

The report displays:

* Registration date
* Number of new users

This helps administrators monitor customer growth.

---

# 23. Custom Date Range Filtering

The Admin Dashboard supports custom date filtering.

Administrators can select:

* From Date
* To Date

The selected range is applied to the dashboard analytics.

The filtering affects revenue, bookings, movie performance, theater performance, peak hours, payment statistics and other date-based reports.

---

# 24. CSV Export

The dashboard provides a CSV export option.

Administrators can export dashboard information for offline analysis.

The CSV report contains sections for:

* Summary
* Booking trends
* Movie performance
* Theater performance
* Peak booking hours
* Payment and refund statistics
* User growth

---

# 25. Admin Authentication and Authorization

The Admin Dashboard is protected using Django authentication and permission mechanisms.

Only authorized administrators can access sensitive dashboard information.

The permission system checks whether the current user is:

* Authenticated
* Staff/superuser
* Or has the required dashboard permission

Unauthorized users are prevented from accessing the dashboard.

---

# 26. Database Optimization and Indexing

To improve dashboard performance, database indexes have been implemented on frequently filtered and queried fields.

### Booking Indexes

* `booked_at`
* `(show, booked_at)`
* `(user, booked_at)`

### Show Indexes

* `(show_date, show_time)`
* `(theater, show_date)`
* `(movie, show_date)`

### PaymentTransaction Indexes

* `(show, status, expires_at)`
* `(status, created_at)`
* `(show, created_at)`
* `(refund_status, refunded_at)`

Additional indexes are also present on frequently queried fields such as booking date, payment status, reservation expiry and show date.

---

# 27. ORM Performance Optimization

The Admin Dashboard uses Django ORM aggregation instead of loading all booking records into Python memory.

The implementation uses operations such as:

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

The database performs the aggregation calculations and returns only the required results.

This avoids unnecessarily loading large numbers of individual booking objects into application memory.

---

# 28. Large Dataset Performance

The dashboard has been designed to work efficiently with large booking datasets, including 100,000 or more bookings.

Performance improvements include:

1. Database indexes reduce unnecessary table scans.
2. Aggregations are performed by the database.
3. Only required summary values are retrieved.
4. Complete booking objects are not loaded unnecessarily.
5. Composite indexes improve multi-field filtering.
6. Date indexes improve custom date-range queries.
7. Payment and refund indexes improve transaction reporting.

This architecture provides better scalability than processing all booking records in Python.

---

# 29. Security

Security features implemented in CineBook include:

* Django authentication
* Login protection
* Permission-based admin access
* CSRF protection where applicable
* Payment verification
* Duplicate booking protection
* Server-side booking validation
* Amount verification
* Restricted dashboard access

Sensitive business analytics are accessible only to authorized administrators.

---

# 30. Admin Credentials

The following credentials are provided for project evaluation.

**Admin Username:** `tanishk233896`

**Admin Password:** `tanishk@9090`

**Admin URL:**
`http://127.0.0.1:8000/admin/`

**Admin Dashboard URL:**
`http://127.0.0.1:8000/admin-dashboard/`


# 31. Project Structure

The main project structure is:

```text
cineBook_django_project/

│
├── bookmyshow/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── ...
│
├── movies/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin_dashboard.py
│   ├── tasks.py
│   ├── management/
│   ├── migrations/
│   └── ...
│
├── static/
│   ├── css/
│   └── images/
│
├── templates/
│
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md
└── REPORT.md
```

---

# 32. Testing and Verification

The following Django commands were used to verify the project:

```text
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

The Django system check completed successfully without reported issues.

The Admin Dashboard was tested for:

* Revenue calculation
* Booking trends
* Movie statistics
* Theater performance
* Occupancy calculation
* Peak hours
* Cancellation statistics
* Refund statistics
* User growth
* Date filtering
* CSV export
* Admin authorization

---

# 33. Sample Admin Dashboard Result

For the tested period from **01/09/2026 to 08/09/2026**, the dashboard displayed:

* Selected Revenue: ₹8,950
* Total Bookings: 37
* Seats Booked: 39
* New Users: 5
* Daily Revenue: ₹1,600
* Weekly Revenue: ₹2,000
* Monthly Revenue: ₹8,950
* Yearly Revenue: ₹8,950

The dashboard also successfully displayed booking trends, movie performance, theater performance, peak booking hours, cancellation/refund statistics and user growth.

---

# 34. Conclusion

CineBook successfully implements an online movie booking platform using Python and Django.

The project provides complete movie discovery, show management, seat booking, payment processing, reviews and ratings, ticket management and administrative analytics.

The Admin Dashboard satisfies the Task 6 requirements by providing business insights, custom date filtering, CSV export, authentication and permission-based access.

Database indexing and Django ORM aggregation have been used to improve performance and scalability for large booking datasets.

The project is therefore suitable for final internship project evaluation and submission.

---

## Project Status

**CineBook – Internship Final Project: COMPLETED**

**Task 6 – Admin Dashboard: COMPLETED**
