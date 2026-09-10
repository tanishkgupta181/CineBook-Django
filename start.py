

import os
import signal
import subprocess
import sys
import time


def main():
    port = os.environ.get("PORT", "8080")

    # ---------------------------------------------------------
    # Start Celery worker
    # ---------------------------------------------------------

    celery = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "bookmyshow.celery:app",
            "worker",
            "--loglevel=info",
            "--pool=solo",
        ]
    )

    # ---------------------------------------------------------
    # Start Django web server
    #
    # Windows:
    #   Django development server
    #
    # Linux / Railway:
    #   Gunicorn
    # ---------------------------------------------------------

    if os.name == "nt":
        web_server = subprocess.Popen(
            [
                sys.executable,
                "manage.py",
                "runserver",
                f"127.0.0.1:{port}",
            ]
        )
    else:
        web_server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "bookmyshow.wsgi:application",
                "--bind",
                f"0.0.0.0:{port}",
                "--workers",
                "1",
            ]
        )

    processes = [celery, web_server]

    # ---------------------------------------------------------
    # Graceful shutdown
    # ---------------------------------------------------------

    def shutdown(signum, frame):
        print("Shutting down services...")

        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                if process.poll() is None:
                    process.kill()

        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    # ---------------------------------------------------------
    # Keep both processes alive
    # ---------------------------------------------------------

    while True:
        time.sleep(2)

        if celery.poll() is not None:
            print("Celery worker stopped.")
            shutdown(signal.SIGTERM, None)

        if web_server.poll() is not None:
            print("Django web server stopped.")
            shutdown(signal.SIGTERM, None)


if __name__ == "__main__":
    main()

