from csv import writer
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, DecimalField, Q, Sum, Value, Max
from django.db.models.functions import (
    Coalesce,
    ExtractHour,
    TruncDay,
    TruncMonth,
    TruncWeek,
    TruncYear,
)
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Booking, PaymentTransaction, Show


# =========================================================
# ADMIN ACCESS
# =========================================================

def admin_dashboard_permission(user):
    """
    Only authenticated staff users and superusers can access
    the admin dashboard.
    """

    return (
        user.is_authenticated
        and user.is_staff
        and (
            user.is_superuser
            or user.has_perm("movies.view_booking")
        )
    )


admin_required = user_passes_test(
    admin_dashboard_permission,
    login_url="/accounts/login/"
)


# =========================================================
# DATE HELPERS
# =========================================================

def parse_dashboard_dates(request):
    today = timezone.localdate()

    start_date = today.replace(day=1)
    end_date = today

    start_value = request.GET.get("start_date")
    end_value = request.GET.get("end_date")

    if start_value:
        try:
            start_date = datetime.strptime(
                start_value,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    if end_value:
        try:
            end_date = datetime.strptime(
                end_value,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            pass

    # Automatically correct reversed dates
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date


def make_datetime_range(start_date, end_date):
    start_dt = timezone.make_aware(
        datetime.combine(
            start_date,
            time.min
        )
    )

    end_dt = timezone.make_aware(
        datetime.combine(
            end_date + timedelta(days=1),
            time.min
        )
    )

    return start_dt, end_dt


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def zero_money():
    return Decimal("0.00")


def calculate_percentage(part, total):
    if not total:
        return 0

    return round(
        (float(part) / float(total)) * 100,
        2
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_required
def admin_dashboard(request):

    # =====================================================
    # DATE FILTER
    # =====================================================

    start_date, end_date = parse_dashboard_dates(request)

    start_dt, end_dt = make_datetime_range(
        start_date,
        end_date
    )

    # =====================================================
    # BASE BOOKING QUERY
    # =====================================================

    bookings = Booking.objects.filter(
        booked_at__gte=start_dt,
        booked_at__lt=end_dt
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    summary = bookings.aggregate(

        total_revenue=Coalesce(
            Sum("total_amount"),
            Value(zero_money()),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2
            )
        ),

        total_bookings=Count("id"),

        total_seats=Coalesce(
            Sum("seats_booked"),
            Value(0)
        ),
    )

    total_revenue = (
        summary["total_revenue"]
        or zero_money()
    )

    total_bookings = (
        summary["total_bookings"]
        or 0
    )

    total_seats = (
        summary["total_seats"]
        or 0
    )

    # =====================================================
    # REVENUE CARDS
    #
    # Daily Revenue uses the latest booking date
    # inside the selected date range.
    # =====================================================

    latest_booking = (
        bookings
        .order_by("-booked_at")
        .first()
    )

    if latest_booking:
        reference_date = timezone.localtime(
            latest_booking.booked_at
        ).date()
    else:
        reference_date = end_date

    # -----------------------------------------------------
    # DAILY REVENUE
    # -----------------------------------------------------

    selected_day_start, selected_day_end = make_datetime_range(
        reference_date,
        reference_date
    )

    revenue_today = (
        Booking.objects
        .filter(
            booked_at__gte=selected_day_start,
            booked_at__lt=selected_day_end
        )
        .aggregate(
            value=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )["value"]
        or zero_money()
    )

    # -----------------------------------------------------
    # WEEKLY REVENUE
    # -----------------------------------------------------

    week_start = reference_date - timedelta(
        days=reference_date.weekday()
    )

    week_start_dt, week_end_dt = make_datetime_range(
        week_start,
        reference_date
    )

    revenue_week = (
        Booking.objects
        .filter(
            booked_at__gte=week_start_dt,
            booked_at__lt=week_end_dt
        )
        .aggregate(
            value=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )["value"]
        or zero_money()
    )

    # -----------------------------------------------------
    # MONTHLY REVENUE
    # -----------------------------------------------------

    month_start = reference_date.replace(
        day=1
    )

    month_start_dt, month_end_dt = make_datetime_range(
        month_start,
        reference_date
    )

    revenue_month = (
        Booking.objects
        .filter(
            booked_at__gte=month_start_dt,
            booked_at__lt=month_end_dt
        )
        .aggregate(
            value=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )["value"]
        or zero_money()
    )

    # -----------------------------------------------------
    # YEARLY REVENUE
    # -----------------------------------------------------

    year_start = reference_date.replace(
        month=1,
        day=1
    )

    year_start_dt, year_end_dt = make_datetime_range(
        year_start,
        reference_date
    )

    revenue_year = (
        Booking.objects
        .filter(
            booked_at__gte=year_start_dt,
            booked_at__lt=year_end_dt
        )
        .aggregate(
            value=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )["value"]
        or zero_money()
    )

    # =====================================================
    # DAILY BOOKING TREND
    # =====================================================

    daily_trend = (
        bookings
        .annotate(
            period=TruncDay("booked_at")
        )
        .values("period")
        .annotate(

            bookings_count=Count("id"),

            seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by("period")
    )

    # =====================================================
    # WEEKLY REVENUE TABLE
    # =====================================================

    weekly_revenue = (
        bookings
        .annotate(
            period=TruncWeek("booked_at")
        )
        .values("period")
        .annotate(

            bookings_count=Count("id"),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by("period")
    )

    # =====================================================
    # MONTHLY REVENUE TABLE
    # =====================================================

    monthly_revenue = (
        bookings
        .annotate(
            period=TruncMonth("booked_at")
        )
        .values("period")
        .annotate(

            bookings_count=Count("id"),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by("period")
    )

    # =====================================================
    # YEARLY REVENUE TABLE
    # =====================================================

    yearly_revenue = (
        bookings
        .annotate(
            period=TruncYear("booked_at")
        )
        .values("period")
        .annotate(

            bookings_count=Count("id"),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by("period")
    )

    # =====================================================
    # MOST BOOKED MOVIES
    # =====================================================

    most_booked_movies = (
        bookings
        .values(
            "show__movie_id",
            "show__movie__title"
        )
        .annotate(

            bookings_count=Count("id"),

            seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by(
            "-seats",
            "-revenue"
        )[:10]
    )

    # =====================================================
    # THEATER PERFORMANCE
    # =====================================================

    theater_capacity = (
        Show.objects
        .filter(
            show_date__gte=start_date,
            show_date__lte=end_date,
            theater_id__isnull=False
        )
        .values(
            "theater_id",
            "theater__name",
            "theater__city"
        )
        .annotate(

            # Capacity of ONE show
            capacity=Coalesce(
                Max("seats"),
                Value(0)
            ),

            # Total shows in selected period
            show_count=Count("id"),

            # Total capacity across all shows
            total_capacity=Coalesce(
                Sum("seats"),
                Value(0)
            )
        )
        .order_by(
            "theater__name"
        )
    )

    # =====================================================
    # THEATER BOOKING DATA
    # =====================================================

    theater_booking_data = (
        Booking.objects
        .filter(
            booked_at__gte=start_dt,
            booked_at__lt=end_dt,
            show__theater_id__isnull=False
        )
        .values(
            "show__theater_id"
        )
        .annotate(

            booked_seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            bookings_count=Count("id"),

            # Number of DIFFERENT shows which received
            # at least one booking.
            booked_show_count=Count(
                "show_id",
                distinct=True
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
    )

    theater_booking_map = {
        row["show__theater_id"]: row
        for row in theater_booking_data
    }

    theater_stats = []

    for theater in theater_capacity:

        theater_id = theater["theater_id"]

        booking_data = theater_booking_map.get(
            theater_id
        )

        # Only show theaters where bookings exist
        if not booking_data:
            continue

        capacity = (
            theater["capacity"]
            or 0
        )

        booked = (
            booking_data.get(
                "booked_seats",
                0
            )
            or 0
        )

        booked_show_count = (
            booking_data.get(
                "booked_show_count",
                0
            )
            or 0
        )

        # -------------------------------------------------
        # OCCUPANCY FIX
        #
        # Occupancy =
        # booked seats /
        # (capacity per show × booked shows)
        #
        # Example:
        # 12 seats / (100 × 1) = 12%
        # -------------------------------------------------

        occupancy_capacity = (
            capacity * booked_show_count
        )

        occupancy = calculate_percentage(
            booked,
            occupancy_capacity
        )

        theater_stats.append(
            {
                "name": (
                    theater["theater__name"]
                    or "Unknown Theater"
                ),

                "city": (
                    theater["theater__city"]
                    or "-"
                ),

                # Capacity of one show
                "capacity": capacity,

                # All shows in selected period
                "show_count": (
                    theater.get(
                        "show_count",
                        0
                    )
                    or 0
                ),

                # Shows which actually received bookings
                "booked_show_count": booked_show_count,

                "booked_seats": booked,

                "bookings_count": (
                    booking_data.get(
                        "bookings_count",
                        0
                    )
                    or 0
                ),

                "revenue": (
                    booking_data.get(
                        "revenue",
                        zero_money()
                    )
                    or zero_money()
                ),

                "occupancy": occupancy,
            }
        )

    theater_stats.sort(
        key=lambda row: (
            row["revenue"],
            row["booked_seats"]
        ),
        reverse=True
    )

    # =====================================================
    # PEAK BOOKING HOURS
    # =====================================================

    peak_booking_hours = (
        bookings
        .annotate(
            hour=ExtractHour("booked_at")
        )
        .values("hour")
        .annotate(

            bookings_count=Count("id"),

            seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by(
            "-bookings_count",
            "-seats"
        )[:10]
    )

    # =====================================================
    # PAYMENT / CANCELLATION / REFUND
    # =====================================================

    transactions = (
        PaymentTransaction.objects
        .filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt
        )
    )

    transaction_stats = transactions.aggregate(

        total_attempts=Count("id"),

        pending=Count(
            "id",
            filter=Q(
                status=PaymentTransaction.STATUS_PENDING
            )
        ),

        successful=Count(
            "id",
            filter=Q(
                status=PaymentTransaction.STATUS_SUCCESS
            )
        ),

        failed=Count(
            "id",
            filter=Q(
                status=PaymentTransaction.STATUS_FAILED
            )
        ),

        cancelled=Count(
            "id",
            filter=Q(
                status=PaymentTransaction.STATUS_CANCELLED
            )
        ),

        cancelled_amount=Coalesce(
            Sum(
                "amount",
                filter=Q(
                    status=PaymentTransaction.STATUS_CANCELLED
                )
            ),
            Value(zero_money()),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2
            )
        ),

        refunded_count=Count(
            "id",
            filter=Q(
                refund_status=(
                    PaymentTransaction.REFUND_COMPLETED
                )
            )
        ),

        refunded_amount=Coalesce(
            Sum(
                "refund_amount",
                filter=Q(
                    refund_status=(
                        PaymentTransaction.REFUND_COMPLETED
                    )
                )
            ),
            Value(zero_money()),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2
            )
        ),
    )

    cancellation_rate = calculate_percentage(
        transaction_stats["cancelled"] or 0,
        transaction_stats["total_attempts"] or 0
    )

    # =====================================================
    # USER GROWTH
    # =====================================================

    user_growth = (
        User.objects
        .filter(
            date_joined__gte=start_dt,
            date_joined__lt=end_dt
        )
        .annotate(
            period=TruncDay("date_joined")
        )
        .values("period")
        .annotate(
            new_users=Count("id")
        )
        .order_by("period")
    )

    total_new_users = (
        User.objects
        .filter(
            date_joined__gte=start_dt,
            date_joined__lt=end_dt
        )
        .count()
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "start_date": start_date,
        "end_date": end_date,

        "total_revenue": total_revenue,
        "total_bookings": total_bookings,
        "total_seats": total_seats,
        "total_new_users": total_new_users,

        "revenue_today": revenue_today,

        # HTML:
        # Daily Revenue (08/09/2026)
        "revenue_day": reference_date,

        "revenue_week": revenue_week,
        "revenue_month": revenue_month,
        "revenue_year": revenue_year,

        "daily_trend": daily_trend,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "yearly_revenue": yearly_revenue,

        "most_booked_movies": most_booked_movies,

        "theater_stats": theater_stats,

        "peak_booking_hours": peak_booking_hours,

        "transaction_stats": transaction_stats,

        "cancellation_rate": cancellation_rate,

        "user_growth": user_growth,
    }

    return render(
        request,
        "admin_dashboard.html",
        context
    )


# =========================================================
# CSV EXPORT
# =========================================================

@admin_required
def admin_dashboard_csv(request):

    start_date, end_date = parse_dashboard_dates(request)

    start_dt, end_dt = make_datetime_range(
        start_date,
        end_date
    )

    bookings = Booking.objects.filter(
        booked_at__gte=start_dt,
        booked_at__lt=end_dt
    )

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        "attachment; "
        f'filename="CineBook_Report_'
        f'{start_date}_{end_date}.csv"'
    )

    csv_writer = writer(response)

    # =====================================================
    # HEADER
    # =====================================================

    csv_writer.writerow(
        ["CINEBOOK ADMIN REPORT"]
    )

    csv_writer.writerow(
        ["From Date", start_date]
    )

    csv_writer.writerow(
        ["To Date", end_date]
    )

    csv_writer.writerow([])

    # =====================================================
    # SUMMARY
    # =====================================================

    summary = bookings.aggregate(

        revenue=Coalesce(
            Sum("total_amount"),
            Value(zero_money()),
            output_field=DecimalField(
                max_digits=12,
                decimal_places=2
            )
        ),

        bookings=Count("id"),

        seats=Coalesce(
            Sum("seats_booked"),
            Value(0)
        )
    )

    csv_writer.writerow(
        ["SUMMARY"]
    )

    csv_writer.writerow(
        [
            "Total Revenue",
            summary["revenue"]
        ]
    )

    csv_writer.writerow(
        [
            "Total Bookings",
            summary["bookings"]
        ]
    )

    csv_writer.writerow(
        [
            "Total Seats",
            summary["seats"]
        ]
    )

    csv_writer.writerow([])

    # =====================================================
    # BOOKING TREND
    # =====================================================

    csv_writer.writerow(
        ["BOOKING TREND"]
    )

    csv_writer.writerow(
        [
            "Date",
            "Bookings",
            "Seats",
            "Revenue"
        ]
    )

    daily_rows = (
        bookings
        .annotate(
            period=TruncDay("booked_at")
        )
        .values("period")
        .annotate(

            bookings_count=Count("id"),

            seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by("period")
    )

    for row in daily_rows.iterator(
        chunk_size=500
    ):

        csv_writer.writerow(
            [
                row["period"],
                row["bookings_count"],
                row["seats"],
                row["revenue"]
            ]
        )

    csv_writer.writerow([])

    # =====================================================
    # MOVIE PERFORMANCE
    # =====================================================

    csv_writer.writerow(
        ["MOST BOOKED MOVIES"]
    )

    csv_writer.writerow(
        [
            "Movie",
            "Bookings",
            "Seats",
            "Revenue"
        ]
    )

    movie_rows = (
        bookings
        .values(
            "show__movie__title"
        )
        .annotate(

            bookings_count=Count("id"),

            seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by(
            "-seats",
            "-revenue"
        )
    )

    for row in movie_rows.iterator(
        chunk_size=500
    ):

        csv_writer.writerow(
            [
                row["show__movie__title"],
                row["bookings_count"],
                row["seats"],
                row["revenue"]
            ]
        )

    csv_writer.writerow([])

    # =====================================================
    # THEATER PERFORMANCE
    # =====================================================

    csv_writer.writerow(
        ["THEATER PERFORMANCE"]
    )

    csv_writer.writerow(
        [
            "Theater",
            "City",
            "Capacity/Show",
            "Shows",
            "Booked Shows",
            "Booked Seats",
            "Occupancy %",
            "Bookings",
            "Revenue"
        ]
    )

    theater_capacity = (
        Show.objects
        .filter(
            show_date__gte=start_date,
            show_date__lte=end_date,
            theater_id__isnull=False
        )
        .values(
            "theater_id",
            "theater__name",
            "theater__city"
        )
        .annotate(

            # Capacity of one show
            capacity=Coalesce(
                Max("seats"),
                Value(0)
            ),

            # Shows in selected period
            show_count=Count("id"),

            # Total capacity
            total_capacity=Coalesce(
                Sum("seats"),
                Value(0)
            )
        )
        .order_by(
            "theater__name"
        )
    )

    theater_bookings = (
        Booking.objects
        .filter(
            booked_at__gte=start_dt,
            booked_at__lt=end_dt,
            show__theater_id__isnull=False
        )
        .values(
            "show__theater_id"
        )
        .annotate(

            booked=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            booking_count=Count("id"),

            # Different shows that received bookings
            booked_show_count=Count(
                "show_id",
                distinct=True
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
    )

    theater_booking_map = {
        row["show__theater_id"]: row
        for row in theater_bookings
    }

    for row in theater_capacity.iterator(
        chunk_size=100
    ):

        theater_id = row["theater_id"]

        booking_data = theater_booking_map.get(
            theater_id
        )

        # Hide theaters with zero bookings
        if not booking_data:
            continue

        capacity = (
            row["capacity"]
            or 0
        )

        booked = (
            booking_data.get(
                "booked",
                0
            )
            or 0
        )

        booked_show_count = (
            booking_data.get(
                "booked_show_count",
                0
            )
            or 0
        )

        # -------------------------------------------------
        # OCCUPANCY FIX
        # -------------------------------------------------

        occupancy_capacity = (
            capacity * booked_show_count
        )

        occupancy = calculate_percentage(
            booked,
            occupancy_capacity
        )

        csv_writer.writerow(
            [
                row["theater__name"]
                or "Unknown Theater",

                row["theater__city"]
                or "-",

                capacity,

                row.get(
                    "show_count",
                    0
                ) or 0,

                booked_show_count,

                booked,

                occupancy,

                booking_data.get(
                    "booking_count",
                    0
                ),

                booking_data.get(
                    "revenue",
                    zero_money()
                )
            ]
        )

    csv_writer.writerow([])

    # =====================================================
    # PEAK HOURS
    # =====================================================

    csv_writer.writerow(
        ["PEAK BOOKING HOURS"]
    )

    csv_writer.writerow(
        [
            "Hour",
            "Bookings",
            "Seats",
            "Revenue"
        ]
    )

    peak_rows = (
        bookings
        .annotate(
            hour=ExtractHour(
                "booked_at"
            )
        )
        .values("hour")
        .annotate(

            bookings_count=Count(
                "id"
            ),

            seats=Coalesce(
                Sum("seats_booked"),
                Value(0)
            ),

            revenue=Coalesce(
                Sum("total_amount"),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
        .order_by(
            "-bookings_count",
            "-seats"
        )
    )

    for row in peak_rows.iterator(
        chunk_size=100
    ):

        if row["hour"] is None:

            hour_display = "-"

        else:

            hour_display = (
                f'{row["hour"]:02d}:00'
            )

        csv_writer.writerow(
            [
                hour_display,
                row["bookings_count"],
                row["seats"],
                row["revenue"]
            ]
        )

    csv_writer.writerow([])

    # =====================================================
    # PAYMENT / REFUND
    # =====================================================

    payment_stats = (
        PaymentTransaction.objects
        .filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt
        )
        .aggregate(

            attempts=Count("id"),

            successful=Count(
                "id",
                filter=Q(
                    status=(
                        PaymentTransaction.STATUS_SUCCESS
                    )
                )
            ),

            failed=Count(
                "id",
                filter=Q(
                    status=(
                        PaymentTransaction.STATUS_FAILED
                    )
                )
            ),

            cancelled=Count(
                "id",
                filter=Q(
                    status=(
                        PaymentTransaction.STATUS_CANCELLED
                    )
                )
            ),

            refunds=Count(
                "id",
                filter=Q(
                    refund_status=(
                        PaymentTransaction.REFUND_COMPLETED
                    )
                )
            ),

            refund_amount=Coalesce(
                Sum(
                    "refund_amount",
                    filter=Q(
                        refund_status=(
                            PaymentTransaction.REFUND_COMPLETED
                        )
                    )
                ),
                Value(zero_money()),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            ),
        )
    )

    csv_writer.writerow(
        ["PAYMENT / CANCELLATION / REFUND"]
    )

    csv_writer.writerow(
        ["Metric", "Value"]
    )

    csv_writer.writerow(
        [
            "Payment Attempts",
            payment_stats["attempts"]
        ]
    )

    csv_writer.writerow(
        [
            "Successful Payments",
            payment_stats["successful"]
        ]
    )

    csv_writer.writerow(
        [
            "Failed Payments",
            payment_stats["failed"]
        ]
    )

    csv_writer.writerow(
        [
            "Cancelled Payments",
            payment_stats["cancelled"]
        ]
    )

    csv_writer.writerow(
        [
            "Completed Refunds",
            payment_stats["refunds"]
        ]
    )

    csv_writer.writerow(
        [
            "Refund Amount",
            payment_stats["refund_amount"]
        ]
    )

    csv_writer.writerow([])

    # =====================================================
    # USER GROWTH
    # =====================================================

    csv_writer.writerow(
        ["USER GROWTH"]
    )

    csv_writer.writerow(
        [
            "Date",
            "New Users"
        ]
    )

    user_rows = (
        User.objects
        .filter(
            date_joined__gte=start_dt,
            date_joined__lt=end_dt
        )
        .annotate(
            period=TruncDay(
                "date_joined"
            )
        )
        .values("period")
        .annotate(
            new_users=Count(
                "id"
            )
        )
        .order_by("period")
    )

    for row in user_rows.iterator(
        chunk_size=500
    ):

        csv_writer.writerow(
            [
                row["period"],
                row["new_users"]
            ]
        )

    return response