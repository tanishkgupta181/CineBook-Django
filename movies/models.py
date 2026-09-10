from uuid import uuid4
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


# =========================================================
# GENRE
# =========================================================

class Genre(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    def __str__(self):
        return self.name


# =========================================================
# LANGUAGE
# =========================================================

class Language(models.Model):

    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )

    def __str__(self):
        return self.name


# =========================================================
# CAST MEMBER
# =========================================================

class CastMember(models.Model):

    name = models.CharField(
        max_length=150,
        db_index=True
    )

    role = models.CharField(
        max_length=150,
        blank=True,
        default=""
    )

    photo_url = models.URLField(
        blank=True,
        default=""
    )

    def __str__(self):
        return self.name


# =========================================================
# MOVIE
# =========================================================

class Movie(models.Model):

    title = models.CharField(
        max_length=255,
        db_index=True
    )

    description = models.TextField(
        blank=True,
        default=""
    )

    genre = models.CharField(
        max_length=100,
        db_index=True
    )

    language = models.CharField(
        max_length=50,
        default="Hindi",
        db_index=True
    )

    genres = models.ManyToManyField(
        Genre,
        blank=True,
        related_name="movies"
    )

    languages = models.ManyToManyField(
        Language,
        blank=True,
        related_name="movies"
    )

    cast_members = models.ManyToManyField(
        CastMember,
        blank=True,
        related_name="movies"
    )

    duration = models.CharField(
        max_length=30,
        default="2h 20m"
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        db_index=True
    )

    trailer_url = models.URLField(
        blank=True,
        default=""
    )

    age_certification = models.CharField(
        max_length=20,
        default="U",
        choices=[
            ("U", "U - Universal"),
            ("UA", "UA - Parental Guidance"),
            ("A", "A - Adults"),
            ("S", "S - Restricted"),
        ]
    )

    poster_url = models.URLField(
        blank=True,
        default=""
    )

    release_date = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )

    popularity = models.IntegerField(
        default=0,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):

        result = self.reviews.aggregate(
            average=Avg("rating")
        )

        average = result["average"]

        if average is None:
            return 0

        return round(float(average), 1)


# =========================================================
# MULTIPLE MOVIE POSTERS
# =========================================================

class MoviePoster(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="posters"
    )

    image_url = models.URLField()

    title = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movie.title} Poster"


# =========================================================
# THEATER
# =========================================================

class Theater(models.Model):

    name = models.CharField(
        max_length=255,
        db_index=True
    )

    city = models.CharField(
        max_length=100,
        db_index=True
    )

    def __str__(self):
        return self.name


# =========================================================
# SHOW
# =========================================================

class Show(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="shows"
    )

    theatre = models.CharField(
        max_length=150,
        blank=True,
        default=""
    )

    theater = models.ForeignKey(
        Theater,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shows"
    )

    show_date = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )

    show_time = models.TimeField(
        db_index=True
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=150
    )

    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=150,
        db_index=True
    )

    seats = models.PositiveIntegerField(
        default=100
    )

    class Meta:
        ordering = ["show_date", "show_time"]

        indexes = [
            models.Index(
                fields=["show_date", "show_time"],
                name="show_date_time_idx"
            ),
            models.Index(
                fields=["theater", "show_date"],
                name="show_theater_date_idx"
            ),
            models.Index(
                fields=["movie", "show_date"],
                name="show_movie_date_idx"
            ),
        ]

    def __str__(self):
        return f"{self.movie.title} - {self.show_time}"


# =========================================================
# USER ACTIVITY
# =========================================================

class UserActivity(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE
    )

    is_booked = models.BooleanField(
        default=False
    )

    viewed_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


# =========================================================
# BOOKING
# =========================================================

class Booking(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    customer_name = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    email = models.EmailField(
        blank=True,
        default=""
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        default=""
    )

    seats_booked = models.PositiveIntegerField(
        default=1
    )

    seat_numbers = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    booking_id = models.UUIDField(
        default=uuid4,
        unique=True,
        editable=False
    )

    payment_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    screen = models.CharField(
        max_length=100,
        default="Screen 1"
    )

    ticket_file = models.FileField(
        upload_to="tickets/",
        null=True,
        blank=True
    )

    booked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ["-booked_at"]

        indexes = [
            models.Index(
                fields=["booked_at"],
                name="booking_booked_at_idx"
            ),
            models.Index(
                fields=["show", "booked_at"],
                name="booking_show_booked_idx"
            ),
            models.Index(
                fields=["user", "booked_at"],
                name="booking_user_booked_idx"
            ),
        ]

    def __str__(self):
        return f"Booking #{self.booking_id}"


# =========================================================
# MOVIE REVIEW + RATING
# =========================================================

class Review(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="movie_reviews"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    review_text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["movie", "user"],
                name="unique_movie_review_per_user"
            )
        ]

        indexes = [
            models.Index(
                fields=["movie", "created_at"],
                name="review_movie_created_idx"
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

    @property
    def is_verified_viewer(self):

        today = timezone.localdate()

        return Booking.objects.filter(
            user=self.user,
            show__movie=self.movie,
            show__show_date__lt=today
        ).exists()


# =========================================================
# REVIEW REPORT
# =========================================================

class ReviewReport(models.Model):

    REPORT_REASONS = [
        ("spam", "Spam"),
        ("offensive", "Offensive Content"),
        ("inappropriate", "Inappropriate Content"),
        ("false", "False Information"),
        ("other", "Other"),
    ]

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="review_reports"
    )

    reason = models.CharField(
        max_length=30,
        choices=REPORT_REASONS
    )

    description = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["review", "reported_by"],
                name="unique_review_report_per_user"
            )
        ]

        indexes = [
            models.Index(
                fields=["created_at"],
                name="review_report_created_idx"
            ),
        ]

    def __str__(self):
        return f"Report - {self.review.movie.title}"


# =========================================================
# PAYMENT TRANSACTION
# =========================================================

class PaymentTransaction(models.Model):

    # -----------------------------------------------------
    # Payment statuses
    # -----------------------------------------------------

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    # -----------------------------------------------------
    # Temporary seat reservation duration
    # -----------------------------------------------------

    RESERVATION_DURATION_MINUTES = 2

    # -----------------------------------------------------
    # Refund statuses
    # -----------------------------------------------------

    REFUND_NONE = "none"
    REFUND_PENDING = "pending"
    REFUND_COMPLETED = "completed"
    REFUND_FAILED = "failed"

    REFUND_STATUS_CHOICES = [
        (REFUND_NONE, "No Refund"),
        (REFUND_PENDING, "Refund Pending"),
        (REFUND_COMPLETED, "Refund Completed"),
        (REFUND_FAILED, "Refund Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payment_transactions"
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="payment_transactions"
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    seat_numbers = models.CharField(
        max_length=255
    )

    customer_name = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    email = models.EmailField(
        blank=True,
        default=""
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        default=""
    )

    screen = models.CharField(
        max_length=100,
        blank=True,
        default="Screen 1"
    )

    # -----------------------------------------------------
    # Reservation expiry
    # -----------------------------------------------------

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Temporary seat reservation expires at this time."
    )

    # -----------------------------------------------------
    # Booking
    # -----------------------------------------------------

    booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transaction"
    )

    # -----------------------------------------------------
    # Failure
    # -----------------------------------------------------

    failure_reason = models.TextField(
        blank=True,
        default=""
    )

    # -----------------------------------------------------
    # Refund information
    # -----------------------------------------------------

    refund_status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default=REFUND_NONE,
        db_index=True
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    refunded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # -----------------------------------------------------
    # Webhook
    # -----------------------------------------------------

    webhook_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["show", "status", "expires_at"],
                name="payment_show_status_exp"
            ),
            models.Index(
                fields=["status", "created_at"],
                name="payment_status_created_idx"
            ),
            models.Index(
                fields=["show", "created_at"],
                name="payment_show_created_idx"
            ),
            models.Index(
                fields=["refund_status", "refunded_at"],
                name="payment_refund_status_idx"
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.razorpay_order_id} - "
            f"{self.status}"
        )

    # =====================================================
    # TASK 5 - RESERVATION HELPERS
    # =====================================================

    @classmethod
    def get_reservation_expiry(cls, start_time=None):

        if start_time is None:
            start_time = timezone.now()

        return (
            start_time
            + timedelta(
                minutes=cls.RESERVATION_DURATION_MINUTES
            )
        )

    @property
    def is_reservation_active(self):

        if self.status != self.STATUS_PENDING:
            return False

        if self.expires_at is None:
            return False

        return timezone.now() < self.expires_at

    @property
    def is_reservation_expired(self):

        if self.status != self.STATUS_PENDING:
            return False

        if self.expires_at is None:
            return False

        return timezone.now() >= self.expires_at

    def set_reservation_expiry(self):

        self.expires_at = self.get_reservation_expiry()

        return self.expires_at

    def release_expired_reservation(self):

        if self.is_reservation_expired:

            self.status = self.STATUS_CANCELLED

            self.failure_reason = (
                "Temporary seat reservation expired after 2 minutes."
            )

            self.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "updated_at",
                ]
            )

            return True

        return False