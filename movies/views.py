

import uuid
import json
from decimal import Decimal
from urllib.parse import urlparse, parse_qs

import razorpay

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Q, Avg, Count
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, serializers

from .models import (
    Movie,
    MoviePoster,
    Theater,
    Show,
    Booking,
    UserActivity,
    Review,
    ReviewReport,
    PaymentTransaction,
)


# =========================================================
# YOUTUBE EMBED URL
# =========================================================

def get_youtube_embed_url(url):
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().split(":")[0]

        allowed_hosts = {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "www.youtu.be",
        }

        if host not in allowed_hosts:
            return ""

        if host in {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
        }:
            if parsed.path.startswith("/embed/"):
                video_id = parsed.path.split(
                    "/embed/",
                    1
                )[1].split("/")[0]

                if video_id:
                    return (
                        "https://www.youtube.com/embed/"
                        f"{video_id}"
                    )

            video_id = parse_qs(
                parsed.query
            ).get("v", [None])[0]

            if video_id:
                return (
                    "https://www.youtube.com/embed/"
                    f"{video_id}"
                )

        if host in {
            "youtu.be",
            "www.youtu.be",
        }:
            video_id = parsed.path.strip(
                "/"
            ).split("/")[0]

            if video_id:
                return (
                    "https://www.youtube.com/embed/"
                    f"{video_id}"
                )

    except Exception:
        pass

    return ""


# =========================================================
# CHECK WHETHER USER HAS WATCHED MOVIE
# =========================================================

def has_watched_movie(user, movie):

    if not user.is_authenticated:
        return False

    today = timezone.localdate()

    return Booking.objects.filter(
        user=user,
        show__movie=movie,
        show__show_date__lt=today
    ).exists()


# =========================================================
# REGISTER
# =========================================================

def register(request):

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Registration successful. Please login."
            )

            return redirect("login")

    else:
        form = UserCreationForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form
        }
    )


# =========================================================
# HOME
# =========================================================

@login_required
def home(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    movies = Movie.objects.all()

    if query:
        movies = movies.filter(
            Q(title__icontains=query)
            |
            Q(description__icontains=query)
            |
            Q(genre__icontains=query)
            |
            Q(language__icontains=query)
            |
            Q(genres__name__icontains=query)
            |
            Q(languages__name__icontains=query)
        ).distinct()

    movies = movies.order_by(
        "-popularity",
        "-created_at"
    )

    return render(
        request,
        "home.html",
        {
            "movies": movies,
            "query": query,
        }
    )


# =========================================================
# MOVIE DETAIL
# =========================================================

@login_required
def movie_detail(request, pk):

    movie = get_object_or_404(
        Movie.objects.prefetch_related(
            "genres",
            "languages",
            "cast_members",
            "reviews",
            "posters",
        ),
        pk=pk
    )

    # -----------------------------------------------------
    # REVIEWS
    # -----------------------------------------------------

    reviews = (
        movie.reviews
        .select_related("user")
        .all()
    )

    average_rating = reviews.aggregate(
        average=Avg("rating")
    )["average"]

    if average_rating is None:
        average_rating = 0

    # -----------------------------------------------------
    # YOUTUBE TRAILER
    # -----------------------------------------------------

    youtube_embed_url = get_youtube_embed_url(
        movie.trailer_url
    )

    # -----------------------------------------------------
    # WATCHED STATUS
    # -----------------------------------------------------

    watched = has_watched_movie(
        request.user,
        movie
    )

    # -----------------------------------------------------
    # POSTERS
    # -----------------------------------------------------

    posters = movie.posters.all()

    # -----------------------------------------------------
    # CAST
    # -----------------------------------------------------

    cast_members = movie.cast_members.all()

    # =====================================================
    # UPCOMING / AVAILABLE SHOWS
    # =====================================================

    today = timezone.localdate()
    current_time = timezone.localtime().time()

    shows = (
        Show.objects
        .filter(
            movie_id=movie.id,
            show_date__gte=today,
        )
        .filter(
            Q(show_date__gt=today)
            |
            Q(
                show_date=today,
                show_time__gte=current_time,
            )
        )
        .select_related(
            "theater"
        )
        .order_by(
            "show_date",
            "theater_id",
            "show_time",
            "id",
        )
    )

    # -----------------------------------------------------
    # DEBUG
    # -----------------------------------------------------

    print("========================================")
    print("MOVIE DETAIL SHOW CHECK")
    print("Movie:", movie.title)
    print("Movie ID:", movie.id)
    print("Today:", today)
    print("Current Time:", current_time)
    print("Upcoming Shows:", shows.count())
    print("========================================")

    # -----------------------------------------------------
    # SIMILAR MOVIES
    # -----------------------------------------------------

    similar_movies = (
        Movie.objects
        .filter(
            Q(genre__iexact=movie.genre)
            |
            Q(language__iexact=movie.language)
            |
            Q(genres__in=movie.genres.all())
            |
            Q(languages__in=movie.languages.all())
        )
        .exclude(
            id=movie.id
        )
        .distinct()
        .order_by(
            "-popularity",
            "-created_at"
        )[:10]
    )

    # -----------------------------------------------------
    # TRENDING MOVIES
    # -----------------------------------------------------

    trending_movies = (
        Movie.objects
        .exclude(
            id=movie.id
        )
        .order_by(
            "-popularity",
            "-created_at"
        )[:10]
    )

    # -----------------------------------------------------
    # RECENTLY RELEASED
    # -----------------------------------------------------

    recently_released = (
        Movie.objects
        .exclude(
            id=movie.id
        )
        .exclude(
            release_date__isnull=True
        )
        .order_by(
            "-release_date"
        )[:10]
    )

    # -----------------------------------------------------
    # USER ACTIVITY
    # -----------------------------------------------------

    UserActivity.objects.create(
        user=request.user,
        movie=movie,
        is_booked=False,
    )

    # -----------------------------------------------------
    # RENDER
    # -----------------------------------------------------

    return render(
        request,
        "movie_detail.html",
        {
            "movie": movie,

            "reviews": reviews,

            "average_rating": round(
                float(average_rating),
                1
            ),

            "youtube_embed_url":
                youtube_embed_url,

            "has_watched":
                watched,

            "posters":
                posters,

            "cast_members":
                cast_members,

            "shows":
                shows,

            "today":
                today,

            "current_time":
                current_time,

            "shows_count":
                shows.count(),

            "similar_movies":
                similar_movies,

            "trending_movies":
                trending_movies,

            "recently_released":
                recently_released,
        }
    )


# =========================================================
# SELECT SHOW
# =========================================================

@login_required
def select_show(request, pk):

    movie = get_object_or_404(
        Movie,
        pk=pk
    )

    today = timezone.localdate()

    shows = (
        Show.objects
        .filter(
            movie_id=movie.id,
            show_date__gte=today
        )
        .select_related(
            "theater"
        )
        .order_by(
            "show_date",
            "show_time"
        )
    )

    print("====================================")
    print("SELECT SHOW")
    print("Movie:", movie.title)
    print("Movie ID:", movie.id)
    print("Today:", today)
    print("Shows Found:", shows.count())
    print("====================================")

    return render(
        request,
        "select_show.html",
        {
            "movie": movie,
            "shows": shows,
        }
    )


# =========================================================
# SUBMIT REVIEW
# =========================================================

@login_required
def submit_review(request, pk):

    movie = get_object_or_404(
        Movie,
        pk=pk
    )

    if request.method != "POST":
        return redirect(
            "movie_detail",
            pk=pk
        )

    if not has_watched_movie(
        request.user,
        movie
    ):
        messages.error(
            request,
            "You can review this movie only after booking and watching it."
        )

        return redirect(
            "movie_detail",
            pk=pk
        )

    rating = request.POST.get("rating")

    review_text = request.POST.get(
        "review_text",
        ""
    ).strip()

    try:
        rating = int(rating)

    except (
        TypeError,
        ValueError
    ):
        messages.error(
            request,
            "Please select a valid rating."
        )

        return redirect(
            "movie_detail",
            pk=pk
        )

    if rating < 1 or rating > 5:
        messages.error(
            request,
            "Rating must be between 1 and 5."
        )

        return redirect(
            "movie_detail",
            pk=pk
        )

    if not review_text:
        messages.error(
            request,
            "Please write a review."
        )

        return redirect(
            "movie_detail",
            pk=pk
        )

    Review.objects.update_or_create(
        movie=movie,
        user=request.user,
        defaults={
            "rating": rating,
            "review_text": review_text,
        }
    )

    messages.success(
        request,
        "Your review has been submitted."
    )

    return redirect(
        "movie_detail",
        pk=pk
    )


# =========================================================
# EDIT REVIEW
# =========================================================

@login_required
def edit_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user
    )

    if not has_watched_movie(
        request.user,
        review.movie
    ):
        messages.error(
            request,
            "You can edit a review only after watching the movie."
        )

        return redirect(
            "movie_detail",
            pk=review.movie.id
        )

    if request.method == "POST":

        rating = request.POST.get("rating")

        review_text = request.POST.get(
            "review_text",
            ""
        ).strip()

        try:
            rating = int(rating)

        except (
            TypeError,
            ValueError
        ):
            messages.error(
                request,
                "Invalid rating."
            )

            return redirect(
                "movie_detail",
                pk=review.movie.id
            )

        if rating < 1 or rating > 5:
            messages.error(
                request,
                "Rating must be between 1 and 5."
            )

            return redirect(
                "movie_detail",
                pk=review.movie.id
            )

        if not review_text:
            messages.error(
                request,
                "Review cannot be empty."
            )

            return redirect(
                "movie_detail",
                pk=review.movie.id
            )

        review.rating = rating
        review.review_text = review_text
        review.save()

        messages.success(
            request,
            "Review updated successfully."
        )

        return redirect(
            "movie_detail",
            pk=review.movie.id
        )

    return render(
        request,
        "edit_review.html",
        {
            "review": review
        }
    )


# =========================================================
# EXPIRE OLD TEMPORARY RESERVATIONS
# =========================================================

def release_expired_reservations(show=None):

    now = timezone.now()

    filters = {
        "status": PaymentTransaction.STATUS_PENDING,
        "expires_at__isnull": False,
        "expires_at__lte": now,
    }

    if show is not None:
        filters["show"] = show

    return (
        PaymentTransaction.objects
        .filter(**filters)
        .update(
            status=PaymentTransaction.STATUS_CANCELLED,
            failure_reason=(
                "Temporary seat reservation expired after 2 minutes."
            ),
            updated_at=now,
        )
    )


# =========================================================
# GET BOOKED SEATS
# =========================================================

def get_booked_seats(show):

    unavailable = set()

    release_expired_reservations(show)

    bookings = (
        Booking.objects
        .filter(
            show=show
        )
        .exclude(
            seat_numbers=""
        )
    )

    for booking in bookings:

        for seat in booking.seat_numbers.split(","):

            seat = seat.strip()

            if seat:
                unavailable.add(seat)

    now = timezone.now()

    pending_transactions = (
        PaymentTransaction.objects
        .filter(
            show=show,
            status=PaymentTransaction.STATUS_PENDING,
            expires_at__gt=now,
        )
        .exclude(
            seat_numbers=""
        )
    )

    for payment in pending_transactions:

        for seat in payment.seat_numbers.split(","):

            seat = seat.strip()

            if seat:
                unavailable.add(seat)

    return unavailable


# =========================================================
# GET AVAILABLE SEATS
# =========================================================

def get_available_seats(show):

    unavailable = get_booked_seats(show)

    return max(
        show.seats - len(unavailable),
        0
    )


# =========================================================
# LIVE SEAT AVAILABILITY
# =========================================================

@login_required
def live_seat_availability(request, show_id):

    with transaction.atomic():

        locked_show = (
            Show.objects
            .select_for_update()
            .get(id=show_id)
        )

        release_expired_reservations(
            locked_show
        )

        now = timezone.now()

        booked_seats = set()

        bookings = (
            Booking.objects
            .filter(
                show=locked_show
            )
            .exclude(
                seat_numbers=""
            )
        )

        for booking in bookings:

            for seat in booking.seat_numbers.split(","):

                seat = seat.strip()

                if seat:
                    booked_seats.add(seat)

        reserved_seats = set()

        active_reservations = (
            PaymentTransaction.objects
            .filter(
                show=locked_show,
                status=PaymentTransaction.STATUS_PENDING,
                expires_at__gt=now,
            )
            .exclude(
                seat_numbers=""
            )
        )

        for payment in active_reservations:

            for seat in payment.seat_numbers.split(","):

                seat = seat.strip()

                if seat:
                    reserved_seats.add(seat)

        my_reserved_seats = set()

        my_reservations = active_reservations.filter(
            user=request.user
        )

        for payment in my_reservations:

            for seat in payment.seat_numbers.split(","):

                seat = seat.strip()

                if seat:
                    my_reserved_seats.add(seat)

        reserved_seats -= booked_seats

        unavailable = (
            booked_seats
            |
            reserved_seats
        )

        available_count = max(
            locked_show.seats - len(unavailable),
            0
        )

        return JsonResponse(
            {
                "success": True,
                "show_id": locked_show.id,

                "booked_seats": sorted(
                    booked_seats
                ),

                "reserved_seats": sorted(
                    reserved_seats
                ),

                "my_reserved_seats": sorted(
                    my_reserved_seats
                ),

                "available_seats": sorted(
                    set(
                        f"A{i}"
                        for i in range(
                            1,
                            locked_show.seats + 1
                        )
                    )
                    - unavailable
                ),

                "available_count":
                    available_count,

                "total_seats":
                    locked_show.seats,

                "reservation_minutes":
                    PaymentTransaction.RESERVATION_DURATION_MINUTES,

                "timestamp":
                    timezone.now().isoformat(),
            }
        )


# =========================================================
# BOOK TICKET / SEAT SELECTION
# =========================================================

@login_required
def book_ticket(request, show_id):

    show = get_object_or_404(
        Show.objects.select_related(
            "movie",
            "theater"
        ),
        id=show_id
    )

    booked_seats = get_booked_seats(show)

    if request.method == "POST":

        selected_seats = request.POST.get(
            "seat_numbers",
            ""
        )

        seat_numbers = [
            seat.strip()
            for seat in selected_seats.split(",")
            if seat.strip()
        ]

        seat_numbers = list(
            dict.fromkeys(
                seat_numbers
            )
        )

        if not seat_numbers:

            messages.error(
                request,
                "Please select at least one seat."
            )

            return redirect(
                "book_ticket",
                show_id=show.id
            )

        invalid_seats = []

        for seat in seat_numbers:

            if len(seat) > 20:
                invalid_seats.append(seat)

        if invalid_seats:

            messages.error(
                request,
                "Invalid seat selection."
            )

            return redirect(
                "book_ticket",
                show_id=show.id
            )

        already_unavailable = [
            seat
            for seat in seat_numbers
            if seat in booked_seats
        ]

        if already_unavailable:

            messages.error(
                request,
                "Some selected seats are already booked or reserved: "
                + ", ".join(already_unavailable)
            )

            return redirect(
                "book_ticket",
                show_id=show.id
            )

        if len(seat_numbers) > show.seats:

            messages.error(
                request,
                "You cannot select more seats than available."
            )

            return redirect(
                "book_ticket",
                show_id=show.id
            )

        return render(
            request,
            "book_ticket.html",
            {
                "show": show,
                "movie": show.movie,
                "booked_seats": list(booked_seats),
                "selected_seats": seat_numbers,
                "total_amount": (
                    Decimal(show.ticket_price)
                    * len(seat_numbers)
                ),
                "reservation_minutes":
                    PaymentTransaction.RESERVATION_DURATION_MINUTES,
            }
        )

    return render(
        request,
        "book_ticket.html",
        {
            "show": show,
            "movie": show.movie,
            "booked_seats": list(booked_seats),
            "selected_seats": [],
            "total_amount": Decimal("0.00"),
            "reservation_minutes":
                PaymentTransaction.RESERVATION_DURATION_MINUTES,
        }
    )


# =========================================================
# RAZORPAY CLIENT
# =========================================================

def get_razorpay_client():

    if not settings.RAZORPAY_KEY_ID:
        raise ValueError(
            "RAZORPAY_KEY_ID is missing."
        )

    if not settings.RAZORPAY_KEY_SECRET:
        raise ValueError(
            "RAZORPAY_KEY_SECRET is missing."
        )

    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )


# =========================================================
# CREATE RAZORPAY ORDER
# =========================================================

@login_required
def create_razorpay_order(request, show_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    seat_numbers_raw = request.POST.get(
        "seat_numbers",
        ""
    )

    seat_numbers = [
        seat.strip()
        for seat in seat_numbers_raw.split(",")
        if seat.strip()
    ]

    seat_numbers = list(
        dict.fromkeys(seat_numbers)
    )

    if not seat_numbers:

        return JsonResponse(
            {
                "success": False,
                "error": "Please select at least one seat."
            },
            status=400
        )

    try:

        with transaction.atomic():

            # IMPORTANT:
            # Do not use select_related("movie", "theater")
            # together with select_for_update() here.
            # PostgreSQL can reject the generated OUTER JOIN
            # with:
            # "FOR UPDATE cannot be applied to the nullable side
            # of an outer join."
            locked_show = (
                Show.objects
                .select_for_update()
                .get(id=show_id)
            )

            release_expired_reservations(
                locked_show
            )

            confirmed_booked_seats = set()

            bookings = (
                Booking.objects
                .filter(
                    show=locked_show
                )
                .exclude(
                    seat_numbers=""
                )
            )

            for booking in bookings:

                for seat in booking.seat_numbers.split(","):

                    seat = seat.strip()

                    if seat:
                        confirmed_booked_seats.add(seat)

            now = timezone.now()

            active_reserved_seats = set()

            pending_transactions = (
                PaymentTransaction.objects
                .filter(
                    show=locked_show,
                    status=PaymentTransaction.STATUS_PENDING,
                    expires_at__gt=now,
                )
                .exclude(
                    seat_numbers=""
                )
            )

            for payment in pending_transactions:

                for seat in payment.seat_numbers.split(","):

                    seat = seat.strip()

                    if seat:
                        active_reserved_seats.add(seat)

            unavailable_seats = (
                confirmed_booked_seats
                |
                active_reserved_seats
            )

            already_unavailable = [
                seat
                for seat in seat_numbers
                if seat in unavailable_seats
            ]

            if already_unavailable:

                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            "These seats are already "
                            "booked or temporarily reserved: "
                            +
                            ", ".join(already_unavailable)
                        )
                    },
                    status=409
                )

            available_count = max(
                locked_show.seats
                - len(unavailable_seats),
                0
            )

            if len(seat_numbers) > available_count:

                return JsonResponse(
                    {
                        "success": False,
                        "error": "Not enough seats available."
                    },
                    status=400
                )

            customer_name = request.POST.get(
                "customer_name",
                request.user.get_full_name()
            ).strip()

            email = request.POST.get(
                "email",
                request.user.email
            ).strip()

            phone = request.POST.get(
                "phone",
                ""
            ).strip()

            screen = request.POST.get(
                "screen",
                "Screen 1"
            ).strip() or "Screen 1"

            total_amount = (
                Decimal(locked_show.ticket_price)
                *
                Decimal(len(seat_numbers))
            )

            amount_paise = int(
                total_amount
                * Decimal("100")
            )

            client = get_razorpay_client()

            order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": (
                        f"cinebook_{locked_show.id}_"
                        f"{request.user.id}_"
                        f"{uuid.uuid4().hex[:10]}"
                    ),
                    "notes": {
                        "show_id": str(locked_show.id),
                        "user_id": str(request.user.id),
                        "seat_numbers": ",".join(seat_numbers),
                        "customer_name": customer_name,
                        "email": email,
                        "phone": phone,
                        "screen": screen,
                    }
                }
            )

            payment_transaction = (
                PaymentTransaction.objects.create(
                    user=request.user,
                    show=locked_show,
                    razorpay_order_id=order["id"],
                    status=PaymentTransaction.STATUS_PENDING,
                    amount=total_amount,
                    seat_numbers=",".join(seat_numbers),
                    customer_name=customer_name,
                    email=email,
                    phone=phone,
                    screen=screen,
                    expires_at=
                        PaymentTransaction.get_reservation_expiry(),
                )
            )

            print(
                "PaymentTransaction created:",
                payment_transaction.id
            )

    except Exception as exc:

        print(
            "Razorpay order creation error:",
            exc
        )

        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Unable to create payment order. "
                    "Please try again."
                )
            },
            status=500
        )

    return JsonResponse(
        {
            "success": True,
            "key": settings.RAZORPAY_KEY_ID,
            "key_id": settings.RAZORPAY_KEY_ID,
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "show_id": locked_show.id,
            "movie": locked_show.movie.title,
            "transaction_id": payment_transaction.id,
            "reservation_minutes":
                PaymentTransaction.RESERVATION_DURATION_MINUTES,
            "expires_at":
                payment_transaction.expires_at.isoformat(),
        }
    )


# =========================================================
# VERIFY RAZORPAY PAYMENT
# =========================================================

@login_required
def verify_razorpay_payment(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    order_id = request.POST.get(
        "razorpay_order_id"
    )

    signature = request.POST.get(
        "razorpay_signature"
    )

    if not payment_id or not order_id or not signature:

        return JsonResponse(
            {
                "success": False,
                "error": "Payment verification data is incomplete."
            },
            status=400
        )

    payment_transaction = (
        PaymentTransaction.objects
        .filter(
            razorpay_order_id=order_id,
            user=request.user
        )
        .first()
    )

    if not payment_transaction:

        return JsonResponse(
            {
                "success": False,
                "error": "Payment transaction not found."
            },
            status=404
        )

    if (
        payment_transaction.status
        == PaymentTransaction.STATUS_SUCCESS
        and payment_transaction.booking
    ):

        return JsonResponse(
            {
                "success": True,
                "message": "Booking already confirmed.",
                "booking_id":
                    str(payment_transaction.booking.booking_id),
                "redirect_url":
                    f"/booking/success/"
                    f"{payment_transaction.booking.booking_id}/",
            }
        )

    try:

        client = get_razorpay_client()

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )

    except Exception:

        payment_transaction.status = (
            PaymentTransaction.STATUS_FAILED
        )

        payment_transaction.failure_reason = (
            "Payment signature verification failed."
        )

        payment_transaction.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

        return JsonResponse(
            {
                "success": False,
                "error": "Payment signature verification failed."
            },
            status=400
        )

    try:

        order = client.order.fetch(order_id)

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "error": "Unable to fetch Razorpay order."
            },
            status=400
        )

    notes = order.get(
        "notes",
        {}
    )

    try:

        order_user_id = int(
            notes.get("user_id")
        )

    except (
        TypeError,
        ValueError
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid payment order information."
            },
            status=400
        )

    if order_user_id != request.user.id:

        return JsonResponse(
            {
                "success": False,
                "error": "Payment does not belong to this user."
            },
            status=403
        )

    try:

        razorpay_amount = int(
            order.get("amount")
        )

    except (
        TypeError,
        ValueError
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid payment amount."
            },
            status=400
        )

    expected_paise = int(
        payment_transaction.amount
        * Decimal("100")
    )

    if razorpay_amount != expected_paise:

        payment_transaction.status = (
            PaymentTransaction.STATUS_FAILED
        )

        payment_transaction.failure_reason = (
            "Payment amount does not match booking amount."
        )

        payment_transaction.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

        return JsonResponse(
            {
                "success": False,
                "error":
                    "Payment amount does not match booking amount."
            },
            status=400
        )

    seat_numbers = [
        seat.strip()
        for seat in payment_transaction.seat_numbers.split(",")
        if seat.strip()
    ]

    seat_numbers = list(
        dict.fromkeys(seat_numbers)
    )

    if not seat_numbers:

        payment_transaction.status = (
            PaymentTransaction.STATUS_FAILED
        )

        payment_transaction.failure_reason = (
            "No seats found for payment."
        )

        payment_transaction.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

        return JsonResponse(
            {
                "success": False,
                "error": "No seats found for payment."
            },
            status=400
        )

    with transaction.atomic():

        locked_transaction = (
            PaymentTransaction.objects
            .select_for_update()
            .select_related(
                "show",
                "show__movie"
            )
            .get(
                id=payment_transaction.id
            )
        )

        if (
            locked_transaction.status
            == PaymentTransaction.STATUS_SUCCESS
            and locked_transaction.booking
        ):

            return JsonResponse(
                {
                    "success": True,
                    "message": "Booking already confirmed.",
                    "booking_id":
                        str(
                            locked_transaction.booking.booking_id
                        ),
                    "redirect_url":
                        f"/booking/success/"
                        f"{locked_transaction.booking.booking_id}/",
                }
            )

        if (
            locked_transaction.status
            != PaymentTransaction.STATUS_PENDING
        ):

            return JsonResponse(
                {
                    "success": False,
                    "error":
                        "This payment reservation is no longer active."
                },
                status=409
            )

        if (
            locked_transaction.expires_at
            and timezone.now()
            >= locked_transaction.expires_at
        ):

            locked_transaction.status = (
                PaymentTransaction.STATUS_CANCELLED
            )

            locked_transaction.failure_reason = (
                "Temporary seat reservation expired before payment verification."
            )

            locked_transaction.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "updated_at",
                ]
            )

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Your 2-minute seat reservation has expired. "
                        "Please select the seats again."
                    )
                },
                status=409
            )

        locked_show = (
            Show.objects
            .select_for_update()
            .get(
                id=locked_transaction.show_id
            )
        )

        confirmed_booked_seats = set()

        bookings = (
            Booking.objects
            .filter(
                show=locked_show
            )
            .exclude(
                seat_numbers=""
            )
        )

        for booking in bookings:

            for seat in booking.seat_numbers.split(","):

                seat = seat.strip()

                if seat:
                    confirmed_booked_seats.add(seat)

        conflict_seats = [
            seat
            for seat in seat_numbers
            if seat in confirmed_booked_seats
        ]

        if conflict_seats:

            locked_transaction.status = (
                PaymentTransaction.STATUS_FAILED
            )

            locked_transaction.failure_reason = (
                "Seats were already booked: "
                + ", ".join(conflict_seats)
            )

            locked_transaction.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "updated_at",
                ]
            )

            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Selected seats are no longer available: "
                        + ", ".join(conflict_seats)
                    )
                },
                status=409
            )

        existing_booking = (
            Booking.objects
            .filter(
                payment_reference=payment_id
            )
            .first()
        )

        if existing_booking:

            locked_transaction.status = (
                PaymentTransaction.STATUS_SUCCESS
            )

            locked_transaction.razorpay_payment_id = payment_id
            locked_transaction.booking = existing_booking

            locked_transaction.save(
                update_fields=[
                    "status",
                    "razorpay_payment_id",
                    "booking",
                    "updated_at",
                ]
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Booking already exists.",
                    "booking_id":
                        str(existing_booking.booking_id),
                    "redirect_url":
                        f"/booking/success/"
                        f"{existing_booking.booking_id}/",
                }
            )

        booking = Booking.objects.create(
            user=request.user,
            show=locked_show,
            customer_name=locked_transaction.customer_name,
            email=locked_transaction.email,
            phone=locked_transaction.phone,
            seats_booked=len(seat_numbers),
            seat_numbers=",".join(seat_numbers),
            total_amount=locked_transaction.amount,
            payment_reference=payment_id,
            screen=locked_transaction.screen,
        )

        locked_transaction.status = (
            PaymentTransaction.STATUS_SUCCESS
        )

        locked_transaction.razorpay_payment_id = payment_id

        locked_transaction.booking = booking

        locked_transaction.save(
            update_fields=[
                "status",
                "razorpay_payment_id",
                "booking",
                "updated_at",
            ]
        )

        UserActivity.objects.create(
            user=request.user,
            movie=locked_show.movie,
            is_booked=True,
        )

    try:

        from .tasks import (
            generate_ticket_and_send_email
        )

        generate_ticket_and_send_email.delay(
            booking.id
        )

    except Exception as exc:

        print(
            "Ticket email task could not be queued:",
            exc
        )

    return JsonResponse(
        {
            "success": True,
            "message":
                "Payment verified and booking confirmed.",
            "booking_id":
                str(booking.booking_id),
            "transaction_id":
                payment_transaction.id,
            "payment_id":
                payment_id,
            "payment_status":
                PaymentTransaction.STATUS_SUCCESS,
            "redirect_url":
                f"/booking/success/"
                f"{booking.booking_id}/",
        }
    )


# =========================================================
# PAYMENT FAILED
# =========================================================

@login_required
def payment_failed(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    order_id = request.POST.get(
        "razorpay_order_id"
    )

    reason = request.POST.get(
        "reason",
        "Payment failed."
    ).strip()

    if not order_id:

        return JsonResponse(
            {
                "success": False,
                "error": "Order ID is required."
            },
            status=400
        )

    with transaction.atomic():

        payment_transaction = (
            PaymentTransaction.objects
            .select_for_update()
            .filter(
                razorpay_order_id=order_id,
                user=request.user
            )
            .first()
        )

        if not payment_transaction:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Payment transaction not found."
                },
                status=404
            )

        if (
            payment_transaction.status
            == PaymentTransaction.STATUS_SUCCESS
        ):

            return JsonResponse(
                {
                    "success": True,
                    "message": "Payment was already successful."
                }
            )

        payment_transaction.status = (
            PaymentTransaction.STATUS_FAILED
        )

        payment_transaction.failure_reason = reason

        payment_transaction.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

    return JsonResponse(
        {
            "success": True,
            "message":
                "Payment failed. Reserved seats released."
        }
    )


# =========================================================
# PAYMENT CANCELLED
# =========================================================

@login_required
def payment_cancelled(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    order_id = request.POST.get(
        "razorpay_order_id"
    )

    if not order_id:

        return JsonResponse(
            {
                "success": False,
                "error": "Order ID is required."
            },
            status=400
        )

    with transaction.atomic():

        payment_transaction = (
            PaymentTransaction.objects
            .select_for_update()
            .filter(
                razorpay_order_id=order_id,
                user=request.user
            )
            .first()
        )

        if not payment_transaction:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Payment transaction not found."
                },
                status=404
            )

        if (
            payment_transaction.status
            == PaymentTransaction.STATUS_SUCCESS
        ):

            return JsonResponse(
                {
                    "success": True,
                    "message": "Payment was already successful."
                }
            )

        payment_transaction.status = (
            PaymentTransaction.STATUS_CANCELLED
        )

        payment_transaction.failure_reason = (
            "Payment cancelled by user."
        )

        payment_transaction.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

    return JsonResponse(
        {
            "success": True,
            "message":
                "Payment cancelled. Reserved seats released."
        }
    )


# =========================================================
# RETRY PAYMENT
# =========================================================

@login_required
def retry_payment(request, transaction_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    old_transaction = get_object_or_404(
        PaymentTransaction,
        id=transaction_id,
        user=request.user
    )

    if (
        old_transaction.status
        == PaymentTransaction.STATUS_SUCCESS
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "This payment is already successful."
            },
            status=400
        )

    try:

        with transaction.atomic():

            # IMPORTANT:
            # Same PostgreSQL FOR UPDATE / OUTER JOIN fix
            # as create_razorpay_order().
            locked_show = (
                Show.objects
                .select_for_update()
                .get(
                    id=old_transaction.show_id
                )
            )

            release_expired_reservations(
                locked_show
            )

            seat_numbers = [
                seat.strip()
                for seat in old_transaction.seat_numbers.split(",")
                if seat.strip()
            ]

            unavailable_seats = get_booked_seats(
                locked_show
            )

            conflict_seats = [
                seat
                for seat in seat_numbers
                if seat in unavailable_seats
            ]

            if conflict_seats:

                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            "These seats are no longer "
                            "available: "
                            +
                            ", ".join(conflict_seats)
                        )
                    },
                    status=409
                )

            amount_paise = int(
                old_transaction.amount
                * Decimal("100")
            )

            client = get_razorpay_client()

            new_order = client.order.create(
                {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": (
                        f"cinebook_retry_"
                        f"{locked_show.id}_"
                        f"{request.user.id}_"
                        f"{uuid.uuid4().hex[:10]}"
                    ),
                    "notes": {
                        "show_id": str(locked_show.id),
                        "user_id": str(request.user.id),
                        "seat_numbers":
                            old_transaction.seat_numbers,
                        "customer_name":
                            old_transaction.customer_name,
                        "email":
                            old_transaction.email,
                        "phone":
                            old_transaction.phone,
                        "screen":
                            old_transaction.screen,
                    }
                }
            )

            new_transaction = (
                PaymentTransaction.objects.create(
                    user=request.user,
                    show=locked_show,
                    razorpay_order_id=new_order["id"],
                    status=PaymentTransaction.STATUS_PENDING,
                    amount=old_transaction.amount,
                    seat_numbers=old_transaction.seat_numbers,
                    customer_name=old_transaction.customer_name,
                    email=old_transaction.email,
                    phone=old_transaction.phone,
                    screen=old_transaction.screen,
                    expires_at=
                        PaymentTransaction.get_reservation_expiry(),
                )
            )

    except Exception as exc:

        print(
            "Retry payment error:",
            exc
        )

        return JsonResponse(
            {
                "success": False,
                "error": "Unable to retry payment."
            },
            status=500
        )

    return JsonResponse(
        {
            "success": True,
            "key": settings.RAZORPAY_KEY_ID,
            "key_id": settings.RAZORPAY_KEY_ID,
            "order_id": new_order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "show_id": locked_show.id,
            "transaction_id": new_transaction.id,
            "reservation_minutes":
                PaymentTransaction.RESERVATION_DURATION_MINUTES,
            "expires_at":
                new_transaction.expires_at.isoformat(),
        }
    )


# =========================================================
# RAZORPAY WEBHOOK
# =========================================================

@csrf_exempt
def razorpay_webhook(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    webhook_signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    if not webhook_signature:

        return JsonResponse(
            {
                "success": False,
                "error": "Webhook signature missing."
            },
            status=400
        )

    webhook_secret = getattr(
        settings,
        "RAZORPAY_WEBHOOK_SECRET",
        ""
    )

    if not webhook_secret:

        return JsonResponse(
            {
                "success": False,
                "error": "Webhook secret is not configured."
            },
            status=500
        )

    try:

        client = get_razorpay_client()

        client.utility.verify_webhook_signature(
            request.body.decode("utf-8"),
            webhook_signature,
            webhook_secret
        )

    except Exception as exc:

        print(
            "Webhook verification failed:",
            exc
        )

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid webhook signature."
            },
            status=400
        )

    try:

        payload = json.loads(
            request.body.decode("utf-8")
        )

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid webhook payload."
            },
            status=400
        )

    event = payload.get(
        "event",
        ""
    )

    payment_entity = (
        payload
        .get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    payment_id = payment_entity.get("id")
    order_id = payment_entity.get("order_id")

    if not order_id:

        return JsonResponse(
            {
                "success": True,
                "message":
                    "Webhook received without order ID."
            }
        )

    with transaction.atomic():

        payment_transaction = (
            PaymentTransaction.objects
            .select_for_update()
            .filter(
                razorpay_order_id=order_id
            )
            .first()
        )

        if not payment_transaction:

            return JsonResponse(
                {
                    "success": True,
                    "message": "Transaction not found."
                }
            )

        if event == "payment.captured":

            if (
                payment_transaction.status
                == PaymentTransaction.STATUS_SUCCESS
            ):

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Webhook already processed."
                    }
                )

            payment_transaction.razorpay_payment_id = payment_id
            payment_transaction.webhook_verified = True

            payment_transaction.save(
                update_fields=[
                    "razorpay_payment_id",
                    "webhook_verified",
                    "updated_at",
                ]
            )

        elif event == "payment.failed":

            if (
                payment_transaction.status
                != PaymentTransaction.STATUS_SUCCESS
            ):

                payment_transaction.status = (
                    PaymentTransaction.STATUS_FAILED
                )

                payment_transaction.razorpay_payment_id = payment_id

                payment_transaction.failure_reason = (
                    payment_entity.get(
                        "error_description"
                    )
                    or
                    "Payment failed."
                )

                payment_transaction.webhook_verified = True

                payment_transaction.save(
                    update_fields=[
                        "status",
                        "razorpay_payment_id",
                        "failure_reason",
                        "webhook_verified",
                        "updated_at",
                    ]
                )

    return JsonResponse(
        {
            "success": True,
            "message": "Webhook processed successfully."
        }
    )


# =========================================================
# BOOKING SUCCESS
# =========================================================

@login_required
def booking_success(request, booking_id):

    booking = get_object_or_404(
        Booking.objects.select_related(
            "show",
            "show__movie",
            "show__theater"
        ),
        booking_id=booking_id,
        user=request.user
    )

    return render(
        request,
        "booking_success.html",
        {
            "booking": booking
        }
    )


# =========================================================
# BOOKING HISTORY
# =========================================================

@login_required
def booking_history(request):

    bookings = (
        Booking.objects
        .filter(
            user=request.user
        )
        .select_related(
            "show",
            "show__movie",
            "show__theater"
        )
        .order_by(
            "-booked_at"
        )
    )

    payment_transactions = (
        PaymentTransaction.objects
        .filter(
            user=request.user
        )
        .exclude(
            status=PaymentTransaction.STATUS_SUCCESS
        )
        .select_related(
            "show",
            "show__movie",
            "show__theater"
        )
        .order_by(
            "-created_at"
        )
    )

    return render(
        request,
        "booking_history.html",
        {
            "bookings": bookings,
            "payment_transactions":
                payment_transactions,
        }
    )


# =========================================================
# REPORT REVIEW
# =========================================================

@login_required
def report_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id
    )

    if request.method != "POST":

        return redirect(
            "movie_detail",
            pk=review.movie.id
        )

    reason = request.POST.get(
        "reason",
        "other"
    )

    description = request.POST.get(
        "description",
        ""
    ).strip()

    valid_reasons = dict(
        ReviewReport.REPORT_REASONS
    )

    if reason not in valid_reasons:

        messages.error(
            request,
            "Invalid report reason."
        )

        return redirect(
            "movie_detail",
            pk=review.movie.id
        )

    if ReviewReport.objects.filter(
        review=review,
        reported_by=request.user
    ).exists():

        messages.warning(
            request,
            "You have already reported this review."
        )

        return redirect(
            "movie_detail",
            pk=review.movie.id
        )

    ReviewReport.objects.create(
        review=review,
        reported_by=request.user,
        reason=reason,
        description=description,
    )

    messages.success(
        request,
        "Review reported successfully."
    )

    return redirect(
        "movie_detail",
        pk=review.movie.id
    )


# =========================================================
# MOVIE DISCOVERY API SERIALIZER
# =========================================================

class MovieDiscoverySerializer(
    serializers.ModelSerializer
):

    average_rating = serializers.SerializerMethodField()

    class Meta:

        model = Movie

        fields = [
            "id",
            "title",
            "description",
            "genre",
            "language",
            "duration",
            "rating",
            "average_rating",
            "trailer_url",
            "age_certification",
            "poster_url",
            "release_date",
            "popularity",
        ]

    def get_average_rating(self, obj):

        return obj.average_rating


# =========================================================
# MOVIE DISCOVERY API
# =========================================================

class MovieDiscoveryView(
    generics.ListAPIView
):

    serializer_class = MovieDiscoverySerializer

    def get_queryset(self):

        queryset = Movie.objects.all()

        search = self.request.GET.get(
            "search",
            ""
        ).strip()

        genre = self.request.GET.get(
            "genre",
            ""
        ).strip()

        language = self.request.GET.get(
            "language",
            ""
        ).strip()

        if search:

            queryset = queryset.filter(
                Q(title__icontains=search)
                |
                Q(description__icontains=search)
                |
                Q(genre__icontains=search)
            )

        if genre:

            queryset = queryset.filter(
                Q(genre__icontains=genre)
                |
                Q(genres__name__icontains=genre)
            )

        if language:

            queryset = queryset.filter(
                Q(language__icontains=language)
                |
                Q(languages__name__icontains=language)
            )

        return (
            queryset
            .distinct()
            .order_by(
                "-popularity",
                "-created_at"
            )
        )


# =========================================================
# DOWNLOAD TICKET
# =========================================================

@login_required
def download_ticket(request, booking_id):

    booking = get_object_or_404(
        Booking,
        booking_id=booking_id,
        user=request.user
    )

    if not booking.ticket_file:

        messages.error(
            request,
            "Ticket is not available yet."
        )

        return redirect(
            "booking_history"
        )

    return FileResponse(
        booking.ticket_file.open("rb"),
        as_attachment=True,
        filename=(
            f"CineBook_Ticket_"
            f"{booking.booking_id}.pdf"
        )
    )
