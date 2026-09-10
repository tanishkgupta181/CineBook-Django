from django.contrib import admin

from .models import (
    Movie,
    Genre,
    Language,
    CastMember,
    MoviePoster,
    Theater,
    Show,
    UserActivity,
    Booking,
    Review,
    ReviewReport,
)


# =========================================================
# MOVIE POSTER INLINE
# =========================================================

class MoviePosterInline(admin.TabularInline):
    model = MoviePoster
    extra = 1

    fields = (
        "image_url",
        "title",
    )


# =========================================================
# MOVIE ADMIN
# =========================================================

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "genre",
        "language",
        "age_certification",
        "duration",
        "rating",
        "average_movie_rating",
        "release_date",
        "popularity",
    )

    list_filter = (
        "genre",
        "language",
        "age_certification",
        "release_date",
    )

    search_fields = (
        "title",
        "genre",
        "language",
        "description",
    )

    filter_horizontal = (
        "genres",
        "languages",
        "cast_members",
    )

    inlines = [
        MoviePosterInline,
    ]

    fieldsets = (
        (
            "Basic Movie Information",
            {
                "fields": (
                    "title",
                    "description",
                    "genre",
                    "language",
                    "genres",
                    "languages",
                    "cast_members",
                )
            },
        ),

        (
            "Movie Details",
            {
                "fields": (
                    "duration",
                    "age_certification",
                    "release_date",
                    "rating",
                    "popularity",
                )
            },
        ),

        (
            "Media & Trailer",
            {
                "fields": (
                    "poster_url",
                    "trailer_url",
                )
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
    )

    @admin.display(
        description="Avg Review Rating",
        ordering="reviews__rating",
    )
    def average_movie_rating(self, obj):
        return obj.average_rating


# =========================================================
# GENRE ADMIN
# =========================================================

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "movie_count",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    @admin.display(description="Movies")
    def movie_count(self, obj):
        return obj.movies.count()


# =========================================================
# LANGUAGE ADMIN
# =========================================================

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "movie_count",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    @admin.display(description="Movies")
    def movie_count(self, obj):
        return obj.movies.count()


# =========================================================
# CAST MEMBER ADMIN
# =========================================================

@admin.register(CastMember)
class CastMemberAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "role",
        "movie_count",
    )

    list_filter = (
        "role",
    )

    search_fields = (
        "name",
        "role",
    )

    ordering = (
        "name",
    )

    @admin.display(description="Movies")
    def movie_count(self, obj):
        return obj.movies.count()


# =========================================================
# MOVIE POSTER ADMIN
# =========================================================

@admin.register(MoviePoster)
class MoviePosterAdmin(admin.ModelAdmin):

    list_display = (
        "movie",
        "title",
        "image_url",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "movie__title",
        "title",
        "image_url",
    )

    autocomplete_fields = (
        "movie",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )


# =========================================================
# THEATER ADMIN
# =========================================================

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "city",
        "show_count",
    )

    list_filter = (
        "city",
    )

    search_fields = (
        "name",
        "city",
    )

    ordering = (
        "city",
        "name",
    )

    @admin.display(description="Shows")
    def show_count(self, obj):
        return obj.shows.count()


# =========================================================
# SHOW ADMIN
# =========================================================

@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):

    list_display = (
        "movie",
        "theater",
        "theatre",
        "show_date",
        "show_time",
        "ticket_price",
        "seats",
        "booked_seat_count",
    )

    list_filter = (
        "theater",
        "show_date",
        "show_time",
    )

    search_fields = (
        "movie__title",
        "theater__name",
        "theatre",
    )

    autocomplete_fields = (
        "movie",
        "theater",
    )

    date_hierarchy = "show_date"

    ordering = (
        "show_date",
        "show_time",
    )

    @admin.display(description="Booked Seats")
    def booked_seat_count(self, obj):
        bookings = obj.bookings.exclude(
            seat_numbers=""
        )

        booked_count = 0

        for booking in bookings:
            seats = [
                seat.strip()
                for seat in booking.seat_numbers.split(",")
                if seat.strip()
            ]

            booked_count += len(seats)

        return booked_count


# =========================================================
# USER ACTIVITY ADMIN
# =========================================================

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "movie",
        "is_booked",
        "viewed_at",
    )

    list_filter = (
        "is_booked",
        "viewed_at",
    )

    search_fields = (
        "user__username",
        "movie__title",
    )

    autocomplete_fields = (
        "user",
        "movie",
    )

    readonly_fields = (
        "viewed_at",
    )

    ordering = (
        "-viewed_at",
    )


# =========================================================
# BOOKING ADMIN
# =========================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "booking_id",
        "user",
        "show",
        "screen",
        "seat_numbers",
        "seats_booked",
        "total_amount",
        "payment_reference",
        "booked_at",
    )

    list_filter = (
        "screen",
        "booked_at",
    )

    search_fields = (
        "booking_id",
        "user__username",
        "customer_name",
        "email",
        "phone",
        "payment_reference",
        "seat_numbers",
    )

    readonly_fields = (
        "booking_id",
        "booked_at",
        "ticket_file",
    )

    autocomplete_fields = (
        "user",
        "show",
    )

    ordering = (
        "-booked_at",
    )


# =========================================================
# REVIEW ADMIN
# =========================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "movie",
        "user",
        "rating",
        "verified_viewer",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "rating",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "movie__title",
        "user__username",
        "review_text",
    )

    autocomplete_fields = (
        "movie",
        "user",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    @admin.display(
        boolean=True,
        description="Verified Viewer",
    )
    def verified_viewer(self, obj):
        return obj.is_verified_viewer


# =========================================================
# REVIEW REPORT ADMIN
# =========================================================

@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):

    list_display = (
        "review",
        "reported_by",
        "reason",
        "created_at",
    )

    list_filter = (
        "reason",
        "created_at",
    )

    search_fields = (
        "review__movie__title",
        "review__user__username",
        "reported_by__username",
        "description",
    )

    autocomplete_fields = (
        "review",
        "reported_by",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )