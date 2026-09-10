from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from movies.models import Movie, Show

class Command(BaseCommand):
    help = "Create sample movies and shows"

    def handle(self, *args, **options):
        samples = [
            ("Sky Warriors", "An action-packed adventure about a young pilot.", "Action", "Hindi", "2h 18m", 8.4),
            ("Love in Jaipur", "A light-hearted romantic comedy set in Jaipur.", "Romance", "Hindi", "2h 05m", 7.9),
            ("The Last Signal", "A science-fiction mystery involving a strange radio signal.", "Sci-Fi", "English", "2h 25m", 8.7),
            ("Campus Days", "Friends, exams and unforgettable college memories.", "Comedy", "Hindi", "2h 10m", 8.1),
        ]

        for title, desc, genre, lang, duration, rating in samples:
            movie, _ = Movie.objects.get_or_create(
                title=title,
                defaults={
                    "description": desc, "genre": genre, "language": lang,
                    "duration": duration, "rating": rating,
                    "poster_url": f"https://placehold.co/600x850?text={title.replace(' ', '+')}"
                },
            )
            for offset, show_time in [(0, time(10,30)), (0, time(14,30)), (0, time(18,30)), (1, time(21,0))]:
                Show.objects.get_or_create(
                    movie=movie,
                    theatre="CineBook PVR, Indore",
                    show_date=date.today() + timedelta(days=offset),
                    show_time=show_time,
                    defaults={"price": 180, "seats": 100},
                )

        self.stdout.write(self.style.SUCCESS("Demo movies and shows created."))
