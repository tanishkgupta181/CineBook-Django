
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from movies.models import Movie, Genre, Language, CastMember, MoviePoster


TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


class Command(BaseCommand):
    help = "Update all movie metadata using TMDB API"

    # ============================================================
    # TMDB API REQUEST
    # ============================================================
    def tmdb_get(self, endpoint, params=None):
        if params is None:
            params = {}

        url = f"{TMDB_BASE_URL}{endpoint}"

        if params:
            url += "?" + urllib.parse.urlencode(params)

        last_error = None

        # Increased retry count for connection reset issues
        for attempt in range(1, 6):
            try:
                self.stdout.write(
                    f"  TMDB request {endpoint} "
                    f"(attempt {attempt}/5)..."
                )

                request = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "Authorization": (
                            f"Bearer {settings.TMDB_API_KEY}"
                        ),
                        "accept": "application/json",
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 "
                            "(KHTML, like Gecko) "
                            "Chrome/150.0 Safari/537.36"
                        ),
                        "Connection": "close",
                    },
                )

                with urllib.request.urlopen(
                    request,
                    timeout=45
                ) as response:

                    data = response.read().decode("utf-8")

                    # Small delay after successful request
                    time.sleep(2)

                    return json.loads(data)

            except Exception as e:
                last_error = e

                self.stdout.write(
                    self.style.WARNING(
                        f"  TMDB request failed: {e}"
                    )
                )

                if attempt < 5:
                    retry_delay = attempt * 4

                    self.stdout.write(
                        f"  Retrying in {retry_delay} seconds..."
                    )

                    time.sleep(retry_delay)

        self.stdout.write(
            self.style.ERROR(
                f"  TMDB request failed after 5 attempts: "
                f"{last_error}"
            )
        )

        return None

    # ============================================================
    # FORMAT DURATION
    # ============================================================
    def format_duration(self, minutes):
        if not minutes:
            return ""

        hours = minutes // 60
        mins = minutes % 60

        if hours and mins:
            return f"{hours}h {mins}m"

        if hours:
            return f"{hours}h"

        return f"{mins}m"

    # ============================================================
    # LANGUAGE
    # ============================================================
    def get_language_name(self, movie_data):
        spoken_languages = movie_data.get(
            "spoken_languages",
            []
        )

        if spoken_languages:
            language = spoken_languages[0].get(
                "english_name"
            )

            if language:
                return language

        code = movie_data.get(
            "original_language",
            ""
        )

        language_map = {
            "hi": "Hindi",
            "en": "English",
            "ta": "Tamil",
            "te": "Telugu",
            "ml": "Malayalam",
            "kn": "Kannada",
            "bn": "Bengali",
            "mr": "Marathi",
            "gu": "Gujarati",
            "pa": "Punjabi",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "it": "Italian",
            "ru": "Russian",
            "pt": "Portuguese",
            "ar": "Arabic",
        }

        return language_map.get(
            code,
            code.upper() if code else "Unknown"
        )

    # ============================================================
    # CERTIFICATION
    # ============================================================
    def get_certification(self, movie_id):
        data = self.tmdb_get(
            f"/movie/{movie_id}/release_dates"
        )

        if not data:
            return None

        country_priority = [
            "IN",
            "US",
            "GB"
        ]

        for country in country_priority:

            for result in data.get(
                "results",
                []
            ):

                if result.get(
                    "iso_3166_1"
                ) != country:
                    continue

                for release in result.get(
                    "release_dates",
                    []
                ):

                    certification = (
                        release.get(
                            "certification",
                            ""
                        )
                        .strip()
                        .upper()
                    )

                    if not certification:
                        continue

                    if certification in [
                        "U",
                        "UA",
                        "A",
                        "S",
                    ]:
                        return certification

                    if certification.startswith("UA"):
                        return "UA"

                    if certification.startswith("U"):
                        return "U"

                    if certification.startswith("A"):
                        return "A"

        return None

    # ============================================================
    # TRAILER
    # ============================================================
    def get_trailer(self, movie_id):
        data = self.tmdb_get(
            f"/movie/{movie_id}/videos",
            {
                "language": "en-US"
            }
        )

        if not data:
            return ""

        videos = data.get(
            "results",
            []
        )

        # Official YouTube trailer first
        for video in videos:

            if (
                video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
                and video.get("official") is True
                and video.get("key")
            ):
                return (
                    "https://www.youtube.com/watch?v="
                    + video["key"]
                )

        # Any YouTube trailer
        for video in videos:

            if (
                video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
                and video.get("key")
            ):
                return (
                    "https://www.youtube.com/watch?v="
                    + video["key"]
                )

        return ""

    # ============================================================
    # CAST
    # ============================================================
    def update_cast(self, movie, movie_id):
        data = self.tmdb_get(
            f"/movie/{movie_id}/credits"
        )

        if not data:
            return

        cast_list = data.get(
            "cast",
            []
        )[:10]

        cast_objects = []

        for person in cast_list:

            name = person.get(
                "name"
            )

            if not name:
                continue

            character = person.get(
                "character",
                ""
            )[:150]

            photo_url = ""

            if person.get(
                "profile_path"
            ):
                photo_url = (
                    f"{IMAGE_BASE_URL}"
                    f"{person['profile_path']}"
                )

            member, created = (
                CastMember.objects.get_or_create(
                    name=name,
                    defaults={
                        "role": character,
                        "photo_url": photo_url,
                    },
                )
            )

            if not created:

                changed = False

                if (
                    character
                    and member.role != character
                ):
                    member.role = character
                    changed = True

                if (
                    photo_url
                    and member.photo_url != photo_url
                ):
                    member.photo_url = photo_url
                    changed = True

                if changed:
                    member.save()

            cast_objects.append(
                member
            )

        if cast_objects:
            movie.cast_members.set(
                cast_objects
            )

    # ============================================================
    # POSTERS
    # ============================================================
    def update_posters(self, movie, movie_id):
        data = self.tmdb_get(
            f"/movie/{movie_id}/images",
            {
                "include_image_language": "en,null"
            }
        )

        if not data:
            return

        posters = data.get(
            "posters",
            []
        )[:5]

        if not posters:
            return

        movie.posters.all().delete()

        for index, poster in enumerate(
            posters,
            start=1
        ):

            file_path = poster.get(
                "file_path"
            )

            if not file_path:
                continue

            MoviePoster.objects.create(
                movie=movie,
                image_url=(
                    f"{IMAGE_BASE_URL}"
                    f"{file_path}"
                ),
                title=f"Poster {index}",
            )

    # ============================================================
    # SEARCH QUERY VARIATIONS
    # ============================================================
    def get_search_queries(self, movie):
        """
        Creates multiple safe search queries for difficult movies.
        Existing movies continue using their normal title first.
        """

        title = movie.title.strip()

        queries = []

        # Normal title
        if title:
            queries.append(title)

        # Title + release year
        if movie.release_date:
            year = movie.release_date.year
            queries.append(f"{title} {year}")

        # Known difficult movie variations
        special_queries = {
            "lucifer": [
                "Lucifer 2019 Malayalam",
                "Lucifer 2019"
            ],

            "manjummel boys": [
                "Manjummel Boys 2024",
                "Manjummel Boys"
            ],

            "premalu": [
                "Premalu 2024",
                "Premalu Malayalam"
            ],

            "kalki 2898 ad": [
                "Kalki 2898 AD 2024",
                "Kalki 2898AD",
                "Kalki 2898 AD"
            ],

            "stree 2": [
                "Stree 2 2024",
                "Stree 2: Sarkate Ka Aatank",
                "Stree 2"
            ],

            "war": [
                "War 2019",
                "War Hindi 2019"
            ],

            "jawan": [
                "Jawan 2023",
                "Jawan Hindi 2023"
            ],
        }

        key = title.lower()

        if key in special_queries:
            queries.extend(
                special_queries[key]
            )

        # Remove duplicates while keeping order
        final_queries = []

        for query in queries:
            if query and query not in final_queries:
                final_queries.append(query)

        return final_queries

    # ============================================================
    # FIND TMDB MOVIE
    # ============================================================
    def find_tmdb_movie(self, movie):

        movie_year = None

        if movie.release_date:
            movie_year = movie.release_date.year

        movie_title_lower = (
            movie.title.strip().lower()
        )

        search_queries = self.get_search_queries(
            movie
        )

        all_results = []

        # --------------------------------------------------------
        # Try multiple search queries
        # --------------------------------------------------------
        for query in search_queries:

            self.stdout.write(
                f"  Searching TMDB for: {query}"
            )

            search_data = self.tmdb_get(
                "/search/movie",
                {
                    "query": query,
                    "language": "en-US",
                    "include_adult": "false",
                    "page": 1,
                },
            )

            if not search_data:
                continue

            results = search_data.get(
                "results",
                []
            )

            if not results:
                continue

            all_results.extend(results)

            # ----------------------------------------------------
            # Exact title + exact year
            # ----------------------------------------------------
            for result in results:

                result_title = (
                    result.get(
                        "title",
                        ""
                    )
                    .strip()
                    .lower()
                )

                release_date = result.get(
                    "release_date",
                    ""
                )

                result_year = None

                if release_date:
                    try:
                        result_year = int(
                            release_date[:4]
                        )
                    except ValueError:
                        pass

                if (
                    result_title
                    == movie_title_lower
                    and movie_year
                    and result_year == movie_year
                ):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Exact TMDB match: "
                            f"{result.get('title')} "
                            f"({result_year})"
                        )
                    )

                    return result

            # ----------------------------------------------------
            # Exact title match
            # ----------------------------------------------------
            for result in results:

                result_title = (
                    result.get(
                        "title",
                        ""
                    )
                    .strip()
                    .lower()
                )

                if (
                    result_title
                    == movie_title_lower
                ):

                    release_date = result.get(
                        "release_date",
                        ""
                    )

                    result_year = None

                    if release_date:
                        try:
                            result_year = int(
                                release_date[:4]
                            )
                        except ValueError:
                            pass

                    # Prefer same year
                    if (
                        not movie_year
                        or result_year == movie_year
                    ):
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  Exact title match: "
                                f"{result.get('title')}"
                            )
                        )

                        return result

        # --------------------------------------------------------
        # Remove duplicate results
        # --------------------------------------------------------
        unique_results = {}

        for result in all_results:

            result_id = result.get("id")

            if result_id:
                unique_results[result_id] = result

        all_results = list(
            unique_results.values()
        )

        if not all_results:
            return None

        # --------------------------------------------------------
        # Strong year match
        # --------------------------------------------------------
        if movie_year:

            year_matches = []

            for result in all_results:

                release_date = result.get(
                    "release_date",
                    ""
                )

                if not release_date:
                    continue

                try:
                    result_year = int(
                        release_date[:4]
                    )

                    if result_year == movie_year:
                        year_matches.append(result)

                except ValueError:
                    continue

            if year_matches:

                # Prefer title containing original title
                for result in year_matches:

                    result_title = (
                        result.get(
                            "title",
                            ""
                        )
                        .strip()
                        .lower()
                    )

                    if (
                        movie_title_lower
                        in result_title
                        or result_title
                        in movie_title_lower
                    ):
                        return result

                return year_matches[0]

        # --------------------------------------------------------
        # Title similarity fallback
        # --------------------------------------------------------
        title_words = set(
            movie_title_lower.split()
        )

        best_result = None
        best_score = 0

        for result in all_results:

            result_title = (
                result.get(
                    "title",
                    ""
                )
                .strip()
                .lower()
            )

            result_words = set(
                result_title.split()
            )

            score = len(
                title_words.intersection(
                    result_words
                )
            )

            if score > best_score:
                best_score = score
                best_result = result

        if best_result:
            self.stdout.write(
                self.style.WARNING(
                    f"  Fallback TMDB match: "
                    f"{best_result.get('title')}"
                )
            )

            return best_result

        return all_results[0]

    # ============================================================
    # UPDATE ONE MOVIE
    # ============================================================
    def update_movie(self, movie):
        self.stdout.write(
            self.style.WARNING(
                f"\nUpdating: {movie.title}"
            )
        )

        # --------------------------------------------------------
        # Find movie
        # --------------------------------------------------------
        search_result = (
            self.find_tmdb_movie(movie)
        )

        if not search_result:

            self.stdout.write(
                self.style.ERROR(
                    f"TMDB movie not found: "
                    f"{movie.title}"
                )
            )

            return False

        tmdb_id = search_result.get(
            "id"
        )

        if not tmdb_id:
            return False

        self.stdout.write(
            f"  Selected TMDB ID: {tmdb_id}"
        )

        self.stdout.write(
            f"  Selected TMDB title: "
            f"{search_result.get('title', '')}"
        )

        # --------------------------------------------------------
        # Get details
        # --------------------------------------------------------
        movie_data = self.tmdb_get(
            f"/movie/{tmdb_id}",
            {
                "language": "en-US"
            }
        )

        if not movie_data:

            self.stdout.write(
                self.style.ERROR(
                    f"Could not get details: "
                    f"{movie.title}"
                )
            )

            return False

        # --------------------------------------------------------
        # Description
        # --------------------------------------------------------
        overview = movie_data.get(
            "overview",
            ""
        )

        if overview:
            movie.description = overview

        # --------------------------------------------------------
        # Release date
        # --------------------------------------------------------
        release_date = movie_data.get(
            "release_date"
        )

        if release_date:

            try:
                movie.release_date = (
                    datetime.strptime(
                        release_date,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:
                pass

        # --------------------------------------------------------
        # Genres
        # --------------------------------------------------------
        tmdb_genres = movie_data.get(
            "genres",
            []
        )

        genre_objects = []

        for genre_data in tmdb_genres:

            genre_name = genre_data.get(
                "name"
            )

            if not genre_name:
                continue

            genre_obj, _ = (
                Genre.objects.get_or_create(
                    name=genre_name
                )
            )

            genre_objects.append(
                genre_obj
            )

        if genre_objects:

            movie.genre = (
                genre_objects[0].name
            )

            movie.genres.set(
                genre_objects
            )

        # --------------------------------------------------------
        # Language
        # --------------------------------------------------------
        language_name = (
            self.get_language_name(
                movie_data
            )
        )

        if language_name:

            movie.language = language_name

            language_obj, _ = (
                Language.objects.get_or_create(
                    name=language_name
                )
            )

            movie.languages.set(
                [language_obj]
            )

        # --------------------------------------------------------
        # Runtime
        # --------------------------------------------------------
        runtime = movie_data.get(
            "runtime"
        )

        if runtime:
            movie.duration = (
                self.format_duration(
                    runtime
                )
            )

        # --------------------------------------------------------
        # Rating
        # --------------------------------------------------------
        vote_average = movie_data.get(
            "vote_average"
        )

        if vote_average is not None:

            try:
                movie.rating = round(
                    float(vote_average),
                    1
                )

            except (
                ValueError,
                TypeError,
            ):
                pass

        # --------------------------------------------------------
        # Popularity
        # --------------------------------------------------------
        popularity = movie_data.get(
            "popularity"
        )

        if popularity is not None:

            try:
                movie.popularity = int(
                    float(popularity)
                )

            except (
                ValueError,
                TypeError,
            ):
                pass

        # --------------------------------------------------------
        # Poster
        # --------------------------------------------------------
        poster_path = movie_data.get(
            "poster_path"
        )

        if poster_path:

            movie.poster_url = (
                f"{IMAGE_BASE_URL}"
                f"{poster_path}"
            )

        # --------------------------------------------------------
        # Certification
        # --------------------------------------------------------
        certification = (
            self.get_certification(
                tmdb_id
            )
        )

        if certification:
            movie.age_certification = (
                certification
            )

        # --------------------------------------------------------
        # Trailer
        # --------------------------------------------------------
        trailer = self.get_trailer(
            tmdb_id
        )

        if trailer:
            movie.trailer_url = trailer

        # --------------------------------------------------------
        # Save movie
        # --------------------------------------------------------
        movie.save()

        # --------------------------------------------------------
        # Cast
        # --------------------------------------------------------
        self.update_cast(
            movie,
            tmdb_id
        )

        # --------------------------------------------------------
        # Posters
        # --------------------------------------------------------
        self.update_posters(
            movie,
            tmdb_id
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated successfully: "
                f"{movie.title}"
            )
        )

        return True

    # ============================================================
    # COMMAND
    # ============================================================
    def handle(self, *args, **options):

        # Check TMDB token
        if not getattr(
            settings,
            "TMDB_API_KEY",
            None
        ):

            self.stdout.write(
                self.style.ERROR(
                    "TMDB_API_KEY is missing "
                    "from settings/.env"
                )
            )

            return

        movies = Movie.objects.all()

        total = movies.count()

        if total == 0:

            self.stdout.write(
                self.style.WARNING(
                    "No movies found in database."
                )
            )

            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {total} movies."
            )
        )

        success = 0
        failed = 0

        # --------------------------------------------------------
        # Update every movie
        # --------------------------------------------------------
        for movie in movies:

            try:

                result = self.update_movie(
                    movie
                )

                if result:
                    success += 1
                else:
                    failed += 1

            except Exception as e:

                failed += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"Error updating "
                        f"{movie.title}: {e}"
                    )
                )

        # --------------------------------------------------------
        # Final result
        # --------------------------------------------------------
        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "===================================="
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Updated: "
                f"{success}, Failed: {failed}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "===================================="
            )
        )