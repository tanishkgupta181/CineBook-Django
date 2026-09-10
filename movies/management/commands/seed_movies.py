import os
import time
import requests

from django.core.management.base import BaseCommand
from movies.models import Movie


TMDB_API_URL = "https://api.themoviedb.org/3/search/movie"


MOVIES = [
    "3 Idiots",
    "Dangal",
    "PK",
    "Taare Zameen Par",
    "Zindagi Na Milegi Dobara",
    "Chhichhore",
    "Shershaah",
    "Drishyam",
    "Drishyam 2",
    "Bhool Bhulaiyaa 2",
    "Jawan",
    "Pathaan",
    "War",
    "Tiger 3",
    "Brahmastra",
    "Animal",
    "Stree 2",
    "Kalki 2898 AD",
    "RRR",
    "Baahubali: The Beginning",
    "Baahubali 2: The Conclusion",
    "Pushpa: The Rise",
    "Pushpa 2: The Rule",
    "Salaar: Part 1 - Ceasefire",
    "KGF: Chapter 1",
    "KGF: Chapter 2",
    "Kantara",
    "Vikram",
    "Leo",
    "Jailer",
    "Master",
    "Kaithi",
    "Premalu",
    "Manjummel Boys",
    "Aavesham",
    "Lucifer",
    "Interstellar",
    "Inception",
    "The Dark Knight",
    "Avengers: Endgame",
    "Avengers: Infinity War",
    "Spider-Man: No Way Home",
    "Avatar",
    "Avatar: The Way of Water",
    "Titanic",
    "The Shawshank Redemption",
    "Forrest Gump",
    "The Matrix",
    "Jurassic Park",
    "The Lord of the Rings: The Return of the King",
]


class Command(BaseCommand):

    help = "Add 50 movies with real TMDB posters"

    def handle(self, *args, **options):

        api_key = os.getenv("TMDB_API_KEY")

        if not api_key:
            self.stdout.write(
                self.style.ERROR(
                    "TMDB_API_KEY not found in .env file."
                )
            )
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json",
        }

        added = 0

        for title in MOVIES:

            success = False

            for attempt in range(1, 4):

                try:

                    self.stdout.write(
                        f"Searching: {title} "
                        f"(attempt {attempt}/3)"
                    )

                    response = requests.get(
                        TMDB_API_URL,
                        headers=headers,
                        params={
                            "query": title,
                            "language": "en-US",
                            "include_adult": "false",
                        },
                        timeout=30,
                    )

                    if response.status_code != 200:

                        self.stdout.write(
                            self.style.ERROR(
                                f"TMDB error for {title}: "
                                f"{response.status_code}"
                            )
                        )

                        break

                    data = response.json()

                    results = data.get("results", [])

                    if not results:

                        self.stdout.write(
                            self.style.WARNING(
                                f"Movie not found: {title}"
                            )
                        )

                        break

                    movie_data = results[0]

                    poster_path = movie_data.get(
                        "poster_path"
                    )

                    if poster_path:

                        poster_url = (
                            "https://image.tmdb.org/t/p/w500"
                            + poster_path
                        )

                    else:

                        poster_url = ""

                    overview = movie_data.get(
                        "overview",
                        ""
                    )

                    rating = movie_data.get(
                        "vote_average",
                        0
                    )

                    release_date = movie_data.get(
                        "release_date"
                    )

                    movie, created = Movie.objects.update_or_create(

                        title=title,

                        defaults={
                            "description": overview,

                            "genre": "Movie",

                            "language": "Hindi",

                            "duration": "2h 20m",

                            "rating": round(
                                float(rating),
                                1
                            ),

                            "poster_url": poster_url,

                            "release_date": (
                                release_date
                                if release_date
                                else None
                            ),

                            "popularity": int(
                                movie_data.get(
                                    "popularity",
                                    0
                                )
                            ),
                        },
                    )

                    added += 1
                    success = True

                    if created:

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Added: {title}"
                            )
                        )

                    else:

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Updated: {title}"
                            )
                        )

                    break

                except requests.RequestException as error:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Network error for {title}: {error}"
                        )
                    )

                    if attempt < 3:

                        self.stdout.write(
                            "Retrying in 3 seconds..."
                        )

                        time.sleep(3)

            if not success:

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed: {title}"
                    )
                )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished! {added} movies processed."
            )
        )