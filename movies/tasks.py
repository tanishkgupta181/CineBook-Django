from io import BytesIO
from urllib.request import Request, urlopen

import qrcode

from celery import shared_task

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import Booking


# ==========================================
# MOVIE POSTER
# ==========================================

def get_movie_poster(movie):

    poster_url = getattr(movie, "poster_url", None)

    if not poster_url:
        return None

    try:
        request = Request(
            poster_url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response = urlopen(
            request,
            timeout=10
        )

        poster_data = response.read()

        poster_buffer = BytesIO(
            poster_data
        )

        poster_buffer.seek(0)

        return poster_buffer

    except Exception:
        return None


# ==========================================
# CELERY TASK
# ==========================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_ticket_and_send_email(self, booking_id):

    # ==========================================
    # GET BOOKING
    # ==========================================

    booking = (
        Booking.objects
        .select_related(
            "user",
            "show__movie",
            "show__theater"
        )
        .get(id=booking_id)
    )

    movie = booking.show.movie
    theater = booking.show.theater

    # ==========================================
    # THEATER
    # ==========================================

    if theater:

        theater_name = theater.name
        theater_city = theater.city

    else:

        theater_name = getattr(
            booking.show,
            "theatre",
            "N/A"
        )

        theater_city = "N/A"

    # ==========================================
    # QR CODE
    # ==========================================

    qr_data = (
        "CineBook Ticket Verification\n"
        f"Booking ID: {booking.booking_id}\n"
        f"Movie: {movie.title}\n"
        f"Seats: {booking.seat_numbers}\n"
        f"Payment: {booking.payment_reference}"
    )

    qr = qrcode.make(qr_data)

    qr_buffer = BytesIO()

    qr.save(
        qr_buffer,
        format="PNG"
    )

    qr_buffer.seek(0)

    # ==========================================
    # MOVIE POSTER
    # ==========================================

    poster_buffer = get_movie_poster(movie)

    # ==========================================
    # PDF
    # ==========================================

    pdf_buffer = BytesIO()

    pdf = canvas.Canvas(
        pdf_buffer,
        pagesize=A4
    )

    width, height = A4

    # ==========================================
    # COLORS
    # ==========================================

    background = colors.HexColor("#090909")
    dark_card = colors.HexColor("#151515")
    red = colors.HexColor("#E50914")
    white = colors.white
    gray_text = colors.HexColor("#AAAAAA")
    green = colors.HexColor("#19A463")

    # ==========================================
    # FULL PAGE BACKGROUND
    # ==========================================

    pdf.setFillColor(background)

    pdf.rect(
        0,
        0,
        width,
        height,
        fill=1,
        stroke=0
    )

    # ==========================================
    # CINEMATIC BACKGROUND SHAPES
    # ==========================================

    pdf.setFillColor(
        colors.HexColor("#180204")
    )

    pdf.circle(
        width - 30,
        height - 80,
        180,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(
        colors.HexColor("#100002")
    )

    pdf.circle(
        20,
        120,
        160,
        fill=1,
        stroke=0
    )

    # ==========================================
    # TOP RED LINE
    # ==========================================

    pdf.setFillColor(red)

    pdf.rect(
        0,
        height - 7,
        width,
        7,
        fill=1,
        stroke=0
    )

    # ==========================================
    # CINEBOOK HEADER
    # ==========================================

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        30
    )

    pdf.drawString(
        38,
        height - 55,
        "CineBook"
    )

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        40,
        height - 72,
        "MOVIE TICKET BOOKING"
    )

    # ==========================================
    # HEADER BADGE
    # ==========================================

    badge_x = width - 175
    badge_y = height - 66

    pdf.setFillColor(green)

    pdf.roundRect(
        badge_x,
        badge_y,
        135,
        25,
        12,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawCentredString(
        badge_x + 67.5,
        badge_y + 8,
        "✓ BOOKING CONFIRMED"
    )

    # ==========================================
    # MAIN TICKET CARD
    # ==========================================

    card_x = 30
    card_y = 45

    card_width = width - 60
    card_height = height - 140

    # ==========================================
    # SHADOW
    # ==========================================

    pdf.setFillColor(
        colors.HexColor("#000000")
    )

    pdf.roundRect(
        card_x + 5,
        card_y - 5,
        card_width,
        card_height,
        18,
        fill=1,
        stroke=0
    )

    # ==========================================
    # CARD
    # ==========================================

    pdf.setFillColor(dark_card)

    pdf.roundRect(
        card_x,
        card_y,
        card_width,
        card_height,
        18,
        fill=1,
        stroke=0
    )

    # ==========================================
    # MOVIE POSTER BOX
    # ==========================================

    poster_x = card_x + 22
    poster_y = height - 350

    poster_width = 145
    poster_height = 195

    pdf.setFillColor(
        colors.HexColor("#252525")
    )

    pdf.roundRect(
        poster_x,
        poster_y,
        poster_width,
        poster_height,
        12,
        fill=1,
        stroke=0
    )

    # ==========================================
    # MOVIE POSTER
    # ==========================================

    if poster_buffer:

        try:

            poster_buffer.seek(0)

            pdf.drawImage(
                ImageReader(poster_buffer),
                poster_x,
                poster_y,
                width=poster_width,
                height=poster_height,
                preserveAspectRatio=False,
                mask="auto"
            )

        except Exception:

            pass

    else:

        # ==========================================
        # POSTER PLACEHOLDER
        # ==========================================

        pdf.setFillColor(red)

        pdf.setFont(
            "Helvetica-Bold",
            18
        )

        pdf.drawCentredString(
            poster_x + poster_width / 2,
            poster_y + 95,
            "CINEBOOK"
        )

        pdf.setFont(
            "Helvetica",
            9
        )

        pdf.setFillColor(white)

        pdf.drawCentredString(
            poster_x + poster_width / 2,
            poster_y + 78,
            "MOVIE TICKET"
        )

    # ==========================================
    # MOVIE INFORMATION
    # ==========================================

    info_x = poster_x + poster_width + 25

    info_y = height - 190

    pdf.setFillColor(red)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info_x,
        info_y,
        "YOUR MOVIE"
    )

    info_y -= 28

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        22
    )

    title = str(
        movie.title or "Movie"
    )

    if len(title) > 30:
        title = title[:30] + "..."

    pdf.drawString(
        info_x,
        info_y,
        title
    )

    info_y -= 27

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        info_x,
        info_y,
        f"{movie.genre or 'N/A'}  •  {movie.language or 'N/A'}"
    )

    info_y -= 18

    pdf.drawString(
        info_x,
        info_y,
        f"Duration: {movie.duration or 'N/A'}"
    )

    # ==========================================
    # THEATER
    # ==========================================

    info_y -= 40

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info_x,
        info_y,
        "THEATER"
    )

    info_y -= 17

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    theater_display = str(
        theater_name or "N/A"
    )

    if len(theater_display) > 25:
        theater_display = theater_display[:25] + "..."

    pdf.drawString(
        info_x,
        info_y,
        theater_display
    )

    info_y -= 16

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        info_x,
        info_y,
        str(theater_city or "N/A")
    )

    # ==========================================
    # DATE + TIME
    # ==========================================

    info_y -= 30

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info_x,
        info_y,
        "DATE & TIME"
    )

    info_y -= 17

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        info_x,
        info_y,
        str(
            booking.show.show_date or "N/A"
        )
    )

    info_y -= 16

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.setFillColor(gray_text)

    pdf.drawString(
        info_x,
        info_y,
        f"Time: {booking.show.show_time}"
    )

    # ==========================================
    # SCREEN
    # ==========================================

    info_y -= 28

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info_x,
        info_y,
        "SCREEN"
    )

    info_y -= 16

    pdf.setFillColor(red)

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        info_x,
        info_y,
        booking.screen or "Screen 1"
    )

    # ==========================================
    # TICKET DETAILS
    # ==========================================
    #
    # IMPORTANT:
    # NO MIDDLE RED DIVIDER IS DRAWN HERE.
    # The old divider code has been completely removed.
    #

    details_y = height - 402

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        14
    )

    pdf.drawString(
        card_x + 25,
        details_y,
        "Ticket Details"
    )

    # ==========================================
    # SEAT BOX
    # ==========================================

    box_y = details_y - 68

    seat_x = card_x + 25

    pdf.setFillColor(
        colors.HexColor("#202020")
    )

    pdf.roundRect(
        seat_x,
        box_y,
        220,
        50,
        9,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        seat_x + 15,
        box_y + 32,
        "SELECTED SEATS"
    )

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        seat_x + 15,
        box_y + 12,
        str(
            booking.seat_numbers or "N/A"
        )[:24]
    )

    # ==========================================
    # SCREEN BOX
    # ==========================================

    screen_x = seat_x + 235

    pdf.setFillColor(
        colors.HexColor("#202020")
    )

    pdf.roundRect(
        screen_x,
        box_y,
        115,
        50,
        9,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        screen_x + 15,
        box_y + 32,
        "SCREEN"
    )

    pdf.setFillColor(red)

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        screen_x + 15,
        box_y + 12,
        str(
            booking.screen or "Screen 1"
        )
    )

    # ==========================================
    # QR CODE
    # ==========================================

    qr_size = 105

    qr_x = card_x + 25
    qr_y = box_y - 145

    # ==========================================
    # QR BACKGROUND
    # ==========================================

    pdf.setFillColor(white)

    pdf.roundRect(
        qr_x - 5,
        qr_y - 5,
        qr_size + 10,
        qr_size + 10,
        8,
        fill=1,
        stroke=0
    )

    qr_buffer.seek(0)

    pdf.drawImage(
        ImageReader(qr_buffer),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto"
    )

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        7
    )

    pdf.drawCentredString(
        qr_x + qr_size / 2,
        qr_y - 17,
        "SCAN TO VERIFY"
    )

    # ==========================================
    # BOOKING INFO
    # ==========================================

    info2_x = qr_x + 145

    info2_y = box_y - 15

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        info2_x,
        info2_y,
        "Booking Information"
    )

    info2_y -= 25

    # ==========================================
    # BOOKING ID
    # ==========================================

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info2_x,
        info2_y,
        "BOOKING ID"
    )

    info2_y -= 15

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        info2_x,
        info2_y,
        str(booking.booking_id)
    )

    # ==========================================
    # PAYMENT
    # ==========================================

    info2_y -= 27

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info2_x,
        info2_y,
        "PAYMENT REFERENCE"
    )

    info2_y -= 15

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        info2_x,
        info2_y,
        str(
            booking.payment_reference or "N/A"
        )[:28]
    )

    # ==========================================
    # CUSTOMER
    # ==========================================

    info2_y -= 27

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica-Bold",
        8
    )

    pdf.drawString(
        info2_x,
        info2_y,
        "CUSTOMER"
    )

    info2_y -= 15

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        info2_x,
        info2_y,
        str(
            booking.customer_name or "Customer"
        )[:28]
    )

    # ==========================================
    # TOTAL AMOUNT
    # ==========================================

    amount_y = 142

    pdf.setFillColor(red)

    pdf.roundRect(
        card_x + 25,
        amount_y,
        card_width - 50,
        52,
        10,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        9
    )

    pdf.drawString(
        card_x + 42,
        amount_y + 31,
        "TOTAL AMOUNT"
    )

    pdf.setFont(
        "Helvetica-Bold",
        19
    )

    pdf.drawRightString(
        width - card_x - 42,
        amount_y + 19,
        f"Rs. {booking.total_amount}"
    )

    # ==========================================
    # FOOTER
    # ==========================================

    pdf.setFillColor(
        colors.HexColor("#222222")
    )

    pdf.roundRect(
        card_x + 20,
        65,
        card_width - 40,
        52,
        10,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(white)

    pdf.setFont(
        "Helvetica-Bold",
        9
    )

    pdf.drawString(
        card_x + 35,
        96,
        "CineBook"
    )

    pdf.setFillColor(gray_text)

    pdf.setFont(
        "Helvetica",
        7
    )

    pdf.drawString(
        card_x + 35,
        80,
        "Please carry this ticket and show the QR code at the theater."
    )

    pdf.drawRightString(
        width - card_x - 35,
        80,
        "Enjoy your movie!"
    )

    # ==========================================
    # BOTTOM RED LINE
    # ==========================================

    pdf.setFillColor(red)

    pdf.rect(
        0,
        0,
        width,
        5,
        fill=1,
        stroke=0
    )

    # ==========================================
    # SAVE PDF
    # ==========================================

    pdf.save()

    pdf_buffer.seek(0)

    # ==========================================
    # SAVE TICKET
    # ==========================================

    filename = (
        f"CineBook_Ticket_"
        f"{booking.booking_id}.pdf"
    )

    booking.ticket_file.save(
        filename,
        ContentFile(
            pdf_buffer.read()
        ),
        save=True
    )

    # ==========================================
    # EMAIL VALIDATION
    # ==========================================

    if not booking.email:

        raise ValueError(
            "Booking email is missing."
        )

    # ==========================================
    # EMAIL BODY
    # ==========================================

    email_body = f"""
Hello {booking.customer_name or 'Customer'},

Your CineBook booking has been confirmed successfully.

Movie:
{movie.title}

Booking ID:
{booking.booking_id}

Theater:
{theater_name}

City:
{theater_city}

Screen:
{booking.screen}

Date:
{booking.show.show_date or 'N/A'}

Time:
{booking.show.show_time}

Seats:
{booking.seat_numbers}

Payment Reference:
{booking.payment_reference}

Total Amount:
Rs. {booking.total_amount}

Your CineBook movie ticket is attached with this email.

Thank you for using CineBook.
Enjoy your movie!
"""

    # ==========================================
    # EMAIL
    # ==========================================

    email = EmailMessage(
        subject=(
            f"CineBook Ticket Confirmation - "
            f"{movie.title}"
        ),
        body=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email],
    )

    # ==========================================
    # ATTACH PDF
    # ==========================================

    booking.ticket_file.open("rb")

    email.attach(
        filename,
        booking.ticket_file.read(),
        "application/pdf"
    )

    booking.ticket_file.close()

    # ==========================================
    # SEND EMAIL
    # ==========================================

    email.send(
        fail_silently=False
    )

    # ==========================================
    # SUCCESS
    # ==========================================

    return {
        "success": True,
        "booking_id": str(
            booking.booking_id
        ),
        "email": booking.email,
    }