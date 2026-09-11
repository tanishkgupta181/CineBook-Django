import base64
from io import BytesIO
from urllib.request import Request, urlopen

import requests
import qrcode

from celery import shared_task

from django.conf import settings
from django.core.files.base import ContentFile

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
        print("No movie poster URL found.")
        return None

    try:

        print("Downloading movie poster...")

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

        print("Movie poster downloaded successfully.")

        return poster_buffer

    except Exception as exc:

        print(
            "Movie poster download failed:",
            repr(exc)
        )

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

    print("=" * 60)
    print("CINEBOOK EMAIL TASK STARTED")
    print("BOOKING ID:", booking_id)
    print("=" * 60)

    # ==========================================
    # GET BOOKING
    # ==========================================

    try:

        booking = (
            Booking.objects
            .select_related(
                "user",
                "show__movie",
                "show__theater"
            )
            .get(id=booking_id)
        )

        print("Booking found successfully.")

    except Exception as exc:

        print(
            "BOOKING FETCH ERROR:",
            repr(exc)
        )

        raise

    movie = booking.show.movie
    theater = booking.show.theater

    print("Movie:", movie.title)
    print("Email:", booking.email)

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

    print("Generating QR code...")

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

    print("QR code generated successfully.")

    # ==========================================
    # MOVIE POSTER
    # ==========================================

    poster_buffer = get_movie_poster(movie)

    # ==========================================
    # PDF
    # ==========================================

    print("Creating PDF ticket...")

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

        except Exception as exc:

            print(
                "Poster drawing failed:",
                repr(exc)
            )

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
    # =========================================

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
    print("Saving PDF...")

    pdf.save()

    pdf_buffer.seek(0)

    # ==========================================
    # SAVE TICKET
    # ==========================================

    filename = (
        f"CineBook_Ticket_"
        f"{booking.booking_id}.pdf"
    )

    print("Saving ticket file:", filename)

    booking.ticket_file.save(
        filename,
        ContentFile(
            pdf_buffer.read()
        ),
        save=True
    )

    print("Ticket PDF saved successfully.")

    # ==========================================
    # EMAIL VALIDATION
    # ==========================================

    if not booking.email:

        raise ValueError(
            "Booking email is missing."
        )

    print("Recipient email:", booking.email)

    # ==========================================
    # RESEND API KEY
    # ==========================================

    resend_api_key = getattr(
        settings,
        "RESEND_API_KEY",
        None
    )

    if not resend_api_key:

        raise ValueError(
            "RESEND_API_KEY is not configured."
        )

    print("RESEND_API_KEY found.")

    # ==========================================
    # READ PDF FOR EMAIL ATTACHMENT
    # ==========================================

    print("Reading PDF attachment...")

    booking.ticket_file.open("rb")

    pdf_data = booking.ticket_file.read()

    booking.ticket_file.close()

    print(
        "PDF attachment size:",
        len(pdf_data),
        "bytes"
    )

    pdf_base64 = base64.b64encode(
        pdf_data
    ).decode("utf-8")

    print("PDF converted to Base64.")

    # ==========================================
    # EMAIL HTML
    # ==========================================

    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>CineBook Ticket Confirmation</title>
    </head>

    <body style="
        margin:0;
        padding:0;
        background:#f4f4f4;
        font-family:Arial,Helvetica,sans-serif;
    ">

        <div style="
            max-width:600px;
            margin:30px auto;
            background:#ffffff;
            border-radius:12px;
            overflow:hidden;
            box-shadow:0 4px 20px rgba(0,0,0,0.10);
        ">

            <div style="
                background:#090909;
                padding:25px 30px;
                border-top:5px solid #E50914;
            ">

                <h1 style="
                    margin:0;
                    color:#ffffff;
                    font-size:30px;
                ">
                    Cine<span style="color:#E50914;">Book</span>
                </h1>

                <p style="
                    margin:5px 0 0;
                    color:#aaaaaa;
                    font-size:12px;
                ">
                    MOVIE TICKET BOOKING
                </p>

            </div>

            <div style="padding:30px;">

                <h2 style="
                    margin-top:0;
                    color:#19A463;
                ">
                    ✓ Booking Confirmed
                </h2>

                <p>
                    Hello
                    <strong>
                        {booking.customer_name or 'Customer'}
                    </strong>,
                </p>

                <p>
                    Your CineBook movie booking has been
                    confirmed successfully.
                </p>

                <p>
                    Your movie ticket is attached to this email.
                </p>

                <hr style="
                    border:0;
                    border-top:1px solid #eeeeee;
                    margin:25px 0;
                ">

                <h3 style="color:#E50914;">
                    Booking Details
                </h3>

                <table style="
                    width:100%;
                    border-collapse:collapse;
                    font-size:14px;
                ">

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Movie
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {movie.title}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Booking ID
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {booking.booking_id}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Theater
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                        ">
                            {theater_name}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            City
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                        ">
                            {theater_city}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Screen
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                        ">
                            {booking.screen}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Date
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                        ">
                            {booking.show.show_date or 'N/A'}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Time
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                        ">
                            {booking.show.show_time}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Seats
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                            font-weight:bold;
                        ">
                            {booking.seat_numbers}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:8px 0;color:#777;">
                            Payment Reference
                        </td>

                        <td style="
                            padding:8px 0;
                            text-align:right;
                        ">
                            {booking.payment_reference}
                        </td>
                    </tr>

                </table>

                <div style="
                    margin-top:25px;
                    padding:18px;
                    background:#E50914;
                    border-radius:8px;
                    color:#ffffff;
                ">

                    <span style="
                        font-size:13px;
                    ">
                        TOTAL AMOUNT
                    </span>

                    <div style="
                        font-size:24px;
                        font-weight:bold;
                        margin-top:5px;
                    ">
                        Rs. {booking.total_amount}
                    </div>

                </div>

                <p style="
                    margin-top:30px;
                    color:#555555;
                ">
                    Thank you for using
                    <strong>CineBook</strong>.
                </p>

                <p style="
                    color:#555555;
                ">
                    Enjoy your movie! 🍿
                </p>

            </div>

            <div style="
                background:#090909;
                padding:18px 30px;
                text-align:center;
                color:#aaaaaa;
                font-size:12px;
            ">
                CineBook • Movie Ticket Booking
            </div>

        </div>

    </body>
    </html>
    """

    # ==========================================
    # SEND EMAIL THROUGH RESEND HTTPS API
    # ==========================================

    print("=" * 60)
    print("SENDING EMAIL THROUGH RESEND HTTPS API")
    print("RECIPIENT:", booking.email)
    print("=" * 60)

    payload = {
        "from": "CineBook <onboarding@resend.dev>",
        "to": [
            booking.email
        ],
        "subject": (
            f"CineBook Ticket Confirmation - "
            f"{movie.title}"
        ),
        "html": email_html,
        "attachments": [
            {
                "filename": filename,
                "content": pdf_base64,
            }
        ],
    }

    try:

        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": (
                    f"Bearer {resend_api_key}"
                ),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        print(
            "RESEND HTTP STATUS:",
            response.status_code
        )

        print(
            "RESEND RESPONSE:",
            response.text[:500]
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        print(
            "RESEND EMAIL ERROR:",
            repr(exc)
        )

        raise

    # ==========================================
    # SUCCESS
    # ==========================================

    print("=" * 60)
    print("CINEBOOK EMAIL TASK COMPLETED SUCCESSFULLY")
    print("BOOKING ID:", booking.booking_id)
    print("EMAIL:", booking.email)
    print("=" * 60)

    return {
        "success": True,
        "booking_id": str(
            booking.booking_id
        ),
        "email": booking.email,
        "email_response": response.text,
    }