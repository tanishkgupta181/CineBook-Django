import time
import urllib.parse
import urllib.request
import json

from django.core.management.base import BaseCommand
from django.conf import settings

from movies.models import Movie
from movies.management.commands.update_movie_metadata import Command as MetadataCommand


# Only the movies that originally failed
FAILED_MOVIES = {
    "Lucifer": 32726,
    "Manjummel Boys": 1012201,
    "Premalu": 1272208,
    "Kalki 2898 AD": 533535,
    "Stree 2": 1112426,
    "War": 585268,
    "Jawan": 872906,
}


class Command(BaseCommand):
    help = "Retry TMDB metadata update only for failed movies"

    def tmdb_get(self, endpoint, params=None):
        if params is None:
            params = {}

        url = "https://api.themoviedb.org/3" + endpoint

        if params:
            url += "?" + urllib.parse.urlencode(params)

        for attempt in range(1, 4):
            try:
                self.stdout.write(
                    f"  TMDB request {endpoint} (attempt {attempt}/3)..."
                )

                request = urllib.request.Request(
                    url,
                    headers={
                        "Authorization": f"Bearer {settings.TMDB_API_KEY}",
                        "accept": "application/json",
                        "User-Agent": "Mozilla/5.0",
                        "Connection": "close",
                    },
                    method="GET",
                )

                with urllib.request.urlopen(
                    request,
                    timeout=45
                ) as response:
                    data = response.read().decode("utf-8")

                time.sleep(1)

                return json.loads(data)

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"  TMDB request failed: {e}"
                    )
                )

                if attempt < 3:
                    time.sleep(3 * attempt)

        return None

    def update_movie(self, movie, tmdb_id):
        self.stdout.write("")
        self.stdout.write(
            self.style.HTTP_INFO(
                f"Updating: {movie.title}"
            )
        )

        self.stdout.write(
            f"  Using TMDB ID: {tmdb_id}"
        )

        details = self.tmdb_get(
            f"/movie/{tmdb_id}",
            {
                "language": "en-US",
            },
        )

        if not details:
            self.stdout.write(
                self.style.ERROR(
                    f"  Could not get details: {movie.title}"
                )
            )
            return False

        helper = MetadataCommand()

        # Basic information
        if details.get("overview"):
            movie.description = details["overview"]

        release_date = details.get("release_date")

        if release_date:
            try:
                from datetime import datetime

                movie.release_date = datetime.strptime(
                    release_date,
                    "%Y-%m-%d"
                ).date()

            except Exception:
                pass

        genres = details.get("genres", [])

        if genres:
            movie.genre = ", ".join(
                g.get("name", "")
                for g in genres
                if g.get("name")
            )

        if details.get("original_language"):
            movie.language = details["original_language"]

        if details.get("runtime"):
            movie.duration = details["runtime"]

        if details.get("vote_average") is not None:
            movie.rating = details["vote_average"]

        if (
            details.get("popularity") is not None
            and hasattr(movie, "popularity")
        ):
            movie.popularity = details["popularity"]

        # Poster
        poster_path = details.get("poster_path")

        if poster_path:
            poster_url = (
                "https://image.tmdb.org/t/p/w500"
                + poster_path
            )

            if hasattr(movie, "poster_url"):
                movie.poster_url = poster_url

            elif hasattr(movie, "poster"):
                movie.poster = poster_url

        # Optional metadata
        try:
            if hasattr(helper, "get_duration"):
                duration = helper.get_duration(details)
                if duration:
                    movie.duration = duration
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Duration skipped: {e}"
                )
            )

        try:
            if hasattr(helper, "get_language"):
                language = helper.get_language(details)
                if language:
                    movie.language = language
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Language skipped: {e}"
                )
            )

        try:
            if hasattr(helper, "get_certification"):
                certification = helper.get_certification(tmdb_id)
                if certification:
                    movie.certification = certification
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Certification skipped: {e}"
                )
            )

        try:
            if hasattr(helper, "get_trailer"):
                trailer = helper.get_trailer(tmdb_id)
                if trailer:
                    movie.trailer_url = trailer
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Trailer skipped: {e}"
                )
            )

        try:
            if hasattr(helper, "get_cast"):
                cast = helper.get_cast(tmdb_id)
                if cast is not None:
                    movie.cast = cast
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Cast skipped: {e}"
                )
            )

        try:
            if hasattr(helper, "get_posters"):
                posters = helper.get_posters(tmdb_id)
                if posters:
                    movie.posters = posters
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  Posters skipped: {e}"
                )
            )

        movie.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Updated successfully: {movie.title}"
            )
        )

        return True

    def handle(self, *args, **options):
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Retrying only the failed movies using direct TMDB IDs..."
            )
        )

        updated = 0
        failed = 0

        for title, tmdb_id in FAILED_MOVIES.items():

            try:
                movie = Movie.objects.get(
                    title__iexact=title
                )

            except Movie.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Movie not found in database: {title}"
                    )
                )
                failed += 1
                continue

            except Movie.MultipleObjectsReturned:
                movie = Movie.objects.filter(
                    title__iexact=title
                ).first()

            try:
                if self.update_movie(movie, tmdb_id):
                    updated += 1
                else:
                    failed += 1

            except Exception as e:
                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"  ERROR: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Updated: {updated}, Failed: {failed}"
            )
        )
        self.stdout.write("=" * 50)