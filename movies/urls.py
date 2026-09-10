
from django.urls import path
from . import views
from . import admin_dashboard


urlpatterns = [

    # =====================================================
    # HOME
    # =====================================================

    path(
        "",
        views.home,
        name="home"
    ),

    # =====================================================
    # AUTHENTICATION
    # =====================================================

    path(
        "register/",
        views.register,
        name="register"
    ),

    # =====================================================
    # MOVIE DETAIL
    # =====================================================

    path(
        "movies/<int:pk>/",
        views.movie_detail,
        name="movie_detail"
    ),

    # =====================================================
    # SHOW / BOOKING
    # =====================================================

    path(
        "book/<int:show_id>/",
        views.book_ticket,
        name="book_ticket"
    ),

    path(
        "select-show/<int:pk>/",
        views.select_show,
        name="select_show"
    ),

    # =====================================================
    # LIVE SEAT AVAILABILITY
    # =====================================================

    path(
        "live-seat-availability/<int:show_id>/",
        views.live_seat_availability,
        name="live_seat_availability"
    ),

    # =====================================================
    # PAYMENT
    # =====================================================

    path(
        "payment/create/<int:show_id>/",
        views.create_razorpay_order,
        name="create_razorpay_order"
    ),

    path(
        "payment/verify/",
        views.verify_razorpay_payment,
        name="verify_razorpay_payment"
    ),

    path(
        "payment/failed/",
        views.payment_failed,
        name="payment_failed"
    ),

    path(
        "payment/cancelled/",
        views.payment_cancelled,
        name="payment_cancelled"
    ),

    path(
        "payment/retry/<int:transaction_id>/",
        views.retry_payment,
        name="retry_payment"
    ),

    path(
        "payment/webhook/",
        views.razorpay_webhook,
        name="razorpay_webhook"
    ),

    # =====================================================
    # BOOKING SUCCESS / HISTORY
    # =====================================================

    path(
        "booking/success/<uuid:booking_id>/",
        views.booking_success,
        name="booking_success"
    ),

    path(
        "booking-history/",
        views.booking_history,
        name="booking_history"
    ),

    # =====================================================
    # TICKET
    # =====================================================

    path(
        "ticket/download/<uuid:booking_id>/",
        views.download_ticket,
        name="download_ticket"
    ),

    # =====================================================
    # REVIEWS
    # =====================================================

    path(
        "movies/<int:pk>/review/",
        views.submit_review,
        name="submit_review"
    ),

    path(
        "review/<int:review_id>/edit/",
        views.edit_review,
        name="edit_review"
    ),

    path(
        "review/<int:review_id>/report/",
        views.report_review,
        name="report_review"
    ),

    # =====================================================
    # MOVIE DISCOVERY API
    # =====================================================

    path(
        "api/movies/",
        views.MovieDiscoveryView.as_view(),
        name="movie-discovery-api"
    ),

    # =====================================================
    # ADMIN DASHBOARD
    # =====================================================

    path(
        "admin-dashboard/",
        admin_dashboard.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin-dashboard/export/",
        admin_dashboard.admin_dashboard_csv,
        name="admin_dashboard_csv"
    ),
]

