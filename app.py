import csv
import json
import uuid
import os
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from openai import OpenAI
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

load_dotenv()

app = Flask(__name__)

# Configure sessions. Set SECRET_KEY in .env and Render before deployment.
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32).hex()

app.config.update(
    MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.getenv("RENDER_SERVICE_ID")),
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# Store customer enquiries in the project directory.
ENQUIRIES_FILE = Path(__file__).resolve().parent / "customer_enquiries.csv"

ENQUIRY_FIELDS = [
    "submitted_at",
    "name",
    "email",
    "phone",
    "service",
    "details",
    "status",
    "attachments",
]

ALLOWED_SERVICES = {
    "Web development",
    "IT support",
    "Business automation",
    "AI chatbot integration",
    "Website maintenance",
    "Other",
}

ALLOWED_STATUSES = {"Pending", "Quoted", "Approved"}
ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_ATTACHMENT_COUNT = 5
ENQUIRY_UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads" / "enquiries"

BUSINESS_INFO = """
Business name: Nexora Business Solutions

Services: Web development, IT support, business automation,
AI chatbot integration and website maintenance.

Business hours: Monday to Friday, 09:00 to 17:00.
Currency: South African Rand (ZAR).

Email: info@example.com.
Phone: +27 00 000 0000.
"""

SYSTEM_PROMPT = f"""
You are a helpful, professional AI business assistant.

Use the following business information to answer questions:
{BUSINESS_INFO}

Be friendly, concise and professional.
Never invent business prices, policies or contact details.
If you do not know an answer, ask the customer to contact the business.
"""


def admin_required(view_function):
    """Require an authenticated admin session for a protected route."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_authenticated"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Please sign in as an administrator."}), 401

            return redirect(url_for("admin_login", next=request.path))

        return view_function(*args, **kwargs)

    return wrapped_view


def ensure_enquiries_schema():
    """Create or update the CSV header while preserving existing enquiries."""
    if not ENQUIRIES_FILE.exists() or ENQUIRIES_FILE.stat().st_size == 0:
        with ENQUIRIES_FILE.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=ENQUIRY_FIELDS
            )
            writer.writeheader()
        return

    with ENQUIRIES_FILE.open(
        "r", newline="", encoding="utf-8"
    ) as csv_file:
        reader = csv.DictReader(csv_file)
        old_fields = list(reader.fieldnames or [])
        rows = list(reader)

    # Preserve existing columns and add any required columns.
    fieldnames = old_fields[:]
    for field in ENQUIRY_FIELDS:
        if field not in fieldnames:
            fieldnames.append(field)

    if fieldnames == old_fields:
        return

    temporary_file = ENQUIRIES_FILE.with_suffix(".csv.tmp")

    try:
        with temporary_file.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()

            for row in rows:
                for field in fieldnames:
                    if row.get(field) is None:
                        row[field] = ""

                if not row.get("status", "").strip():
                    row["status"] = "Pending"

                writer.writerow(row)

        temporary_file.replace(ENQUIRIES_FILE)

    except OSError:
        if temporary_file.exists():
            temporary_file.unlink()
        raise


def basic_reply(message):
    """Provide demonstration responses when AI is unavailable."""
    text = message.lower()

    if any(word in text for word in ["hello", "hi", "hey"]):
        return (
            "Hello! Welcome to Nexora Business Solutions. "
            "How can I help you today?"
        )

    if any(word in text for word in ["service", "services", "offer"]):
        return (
            "We offer web development, IT support, business "
            "automation, AI chatbot integration and website "
            "maintenance. Which service interests you?"
        )

    if any(word in text for word in ["hour", "open", "closing"]):
        return (
            "Our listed business hours are Monday to Friday, "
            "09:00 to 17:00."
        )

    if any(word in text for word in ["price", "cost", "quote"]):
        return (
            "Pricing depends on the service you need. "
            "Please submit our customer enquiry form so your "
            "requirements can be reviewed for a quotation."
        )

    if any(word in text for word in ["contact", "email", "phone"]):
        return (
            "Our displayed demonstration contact details are "
            "info@example.com and +27 00 000 0000. "
            "These should be replaced with your real business details."
        )

    return (
        "Thanks for your message! I can help with our services, "
        "business hours, pricing enquiries and contact information. "
        "What would you like to know?"
    )


def generate_reply(message, history):
    """Use OpenAI when available; otherwise provide a demo response."""
    if client is None:
        return basic_reply(message)

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        for item in history[-10:]:
            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")

                if role in ("user", "assistant") and isinstance(content, str):
                    messages.append({
                        "role": role,
                        "content": content[:3000],
                    })

        messages.append({
            "role": "user",
            "content": message,
        })

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        reply = response.choices[0].message.content
        return reply if reply else basic_reply(message)

    except Exception:
        app.logger.exception(
            "AI request failed; using the demo response instead."
        )
        return basic_reply(message)


@app.route("/")
def home():
    """Display the public chatbot and enquiry form."""
    return render_template("index.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Display the admin login form and authenticate an administrator."""
    if session.get("admin_authenticated"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Do not allow access until credentials are configured.
        if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
            return render_template(
                "admin_login.html",
                error="Admin login is not configured yet. Please configure the admin environment variables.",
            ), 503

        try:
            password_is_valid = check_password_hash(
                ADMIN_PASSWORD_HASH, password
            )
        except (ValueError, TypeError):
            app.logger.error("ADMIN_PASSWORD_HASH is invalid.")
            password_is_valid = False

        if username == ADMIN_USERNAME and password_is_valid:
            session.clear()
            session["admin_authenticated"] = True
            session["admin_username"] = username
            session.permanent = True

            destination = request.args.get("next", "")
            # Only permit local relative destinations to prevent open redirects.
            if (
                destination.startswith("/")
                and not destination.startswith("//")
                and not destination.startswith("/\\")
            ):
                return redirect(destination)

            return redirect(url_for("admin_dashboard"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password. Please try again.",
        ), 401

    return render_template("admin_login.html", error=None)


@app.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    """End the admin session."""
    session.clear()
    return redirect(url_for("admin_login"))


def parse_attachment_records(raw_value):
    """Parse stored attachment metadata safely for the admin dashboard."""
    if not raw_value:
        return []

    try:
        records = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(records, list):
        return []

    safe_records = []
    for record in records:
        if not isinstance(record, dict):
            continue
        original_name = record.get("original_name")
        stored_name = record.get("stored_name")
        if not isinstance(original_name, str) or not isinstance(stored_name, str):
            continue
        # Stored names are generated UUIDs with an allowed extension.
        if secure_filename(stored_name) != stored_name:
            continue
        if Path(stored_name).suffix.lower() not in ALLOWED_ATTACHMENT_EXTENSIONS:
            continue
        safe_records.append({
            "original_name": original_name,
            "stored_name": stored_name,
            "size_bytes": record.get("size_bytes", 0),
        })
    return safe_records


@app.route("/admin")
@admin_required
def admin_dashboard():
    """Display saved enquiries to an authenticated administrator."""
    enquiries = []

    try:
        if ENQUIRIES_FILE.exists():
            with ENQUIRIES_FILE.open(
                "r", newline="", encoding="utf-8"
            ) as csv_file:
                reader = csv.DictReader(csv_file)

                for index, row in enumerate(reader):
                    enquiries.append({
                        # ID is the row's original position in the CSV.
                        "id": index,
                        "submitted_at": row.get("submitted_at", ""),
                        "name": row.get("name", ""),
                        "email": row.get("email", ""),
                        "phone": row.get("phone", ""),
                        "service": row.get("service", ""),
                        "details": row.get("details", ""),
                        "status": (
                            row.get("status", "").strip() or "Pending"
                        ),
                        "attachments": parse_attachment_records(
                            row.get("attachments", "")
                        ),
                    })

    except (OSError, csv.Error):
        app.logger.exception("Could not read customer enquiries")
        abort(500)

    # Show newest enquiries first while retaining their original CSV IDs.
    enquiries.reverse()

    counts = {
        "pending": sum(
            1 for item in enquiries
            if item["status"].lower() == "pending"
        ),
        "quoted": sum(
            1 for item in enquiries
            if item["status"].lower() == "quoted"
        ),
        "approved": sum(
            1 for item in enquiries
            if item["status"].lower() == "approved"
        ),
    }

    return render_template(
        "admin.html",
        enquiries=enquiries,
        counts=counts,
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """Receive a chatbot message and return its response."""
    data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request."}), 400

    message = data.get("message", "")
    history = data.get("history", [])

    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Please enter a message."}), 400

    if len(message) > 3000:
        return jsonify({"error": "Your message is too long."}), 400

    if not isinstance(history, list):
        history = []

    try:
        reply = generate_reply(message.strip(), history)

        return jsonify({
            "reply": reply,
            "mode": "ai" if client else "demo",
        })

    except Exception:
        app.logger.exception("Chat request failed")
        return jsonify({
            "error": "The chatbot could not respond. Please try again."
        }), 500



@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(error):
    return jsonify({
        "error": "The total upload must be 20 MB or smaller."
    }), 413


@app.route("/api/enquiry", methods=["POST"])
def submit_enquiry():
    """Validate and save an enquiry submitted as JSON or FormData."""
    if request.is_json:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Please submit the enquiry form correctly."}), 400
    else:
        data = request.form

    fields = {}
    for field in ("name", "email", "phone", "service", "details"):
        value = data.get(field, "")
        if not isinstance(value, str):
            return jsonify({"error": f"The {field} field must be text."}), 400
        fields[field] = value.strip()

    name, email, phone = fields["name"], fields["email"], fields["phone"]
    service, details = fields["service"], fields["details"]

    if not name or not email or not service or not details:
        return jsonify({"error": "Please complete all required fields."}), 400
    if len(name) > 100:
        return jsonify({"error": "Name must be 100 characters or fewer."}), 400
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "Please enter a valid email address."}), 400
    if len(phone) > 30:
        return jsonify({"error": "Phone number must be 30 characters or fewer."}), 400
    if service not in ALLOWED_SERVICES:
        return jsonify({"error": "Please choose a valid service."}), 400
    if len(details) > 3000:
        return jsonify({"error": "Project details must be 3000 characters or fewer."}), 400

    files = [
        item for item in request.files.getlist("attachments")
        if item and item.filename and item.filename.strip()
    ]
    if len(files) > MAX_ATTACHMENT_COUNT:
        return jsonify({"error": "You can attach a maximum of 5 files."}), 400

    validated = []
    for item in files:
        safe_original = secure_filename(item.filename)
        extension = Path(safe_original).suffix.lower()
        if not safe_original or extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
            return jsonify({
                "error": "Choose PDF, JPG, JPEG, PNG or DOCX files only."
            }), 400

        item.stream.seek(0, 2)
        size = item.stream.tell()
        item.stream.seek(0)
        if size > MAX_ATTACHMENT_BYTES:
            return jsonify({
                "error": f"{safe_original} exceeds the 5 MB per-file limit."
            }), 400
        validated.append((item, safe_original, extension, size))

    saved_paths = []
    attachment_records = []

    try:
        ensure_enquiries_schema()

        if validated:
            ENQUIRY_UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

        for item, original_name, extension, size in validated:
            stored_name = uuid.uuid4().hex + extension
            destination = ENQUIRY_UPLOAD_FOLDER / stored_name
            item.save(destination)
            saved_paths.append(destination)
            attachment_records.append({
                "original_name": original_name,
                "stored_name": stored_name,
                "size_bytes": size,
            })

        with ENQUIRIES_FILE.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=ENQUIRY_FIELDS, extrasaction="ignore"
            )
            writer.writerow({
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "name": name,
                "email": email,
                "phone": phone,
                "service": service,
                "details": details,
                "status": "Pending",
                "attachments": json.dumps(attachment_records, ensure_ascii=False),
            })

    except (OSError, csv.Error):
        for saved_path in saved_paths:
            try:
                saved_path.unlink(missing_ok=True)
            except OSError:
                app.logger.exception("Could not clean up an uploaded file")
        app.logger.exception("Could not save customer enquiry")
        return jsonify({
            "error": "We could not save your enquiry right now. Please try again later."
        }), 500

    app.logger.info("A customer enquiry was saved successfully.")
    return jsonify({
        "message": (
            "Thank you! Your enquiry has been received. "
            "Your quotation request is awaiting review."
        )
    }), 201

@app.route("/admin/enquiry/<int:enquiry_id>/attachment/<path:stored_name>")
@admin_required
def download_enquiry_attachment(enquiry_id, stored_name):
    """Serve an attachment only when it belongs to a saved enquiry."""
    if not ENQUIRIES_FILE.exists():
        abort(404)

    try:
        with ENQUIRIES_FILE.open("r", newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
    except (OSError, csv.Error):
        app.logger.exception("Could not read enquiries for attachment download")
        abort(500)

    if enquiry_id < 0 or enquiry_id >= len(rows):
        abort(404)

    attachment_records = parse_attachment_records(
        rows[enquiry_id].get("attachments", "")
    )
    permitted = any(
        item["stored_name"] == stored_name for item in attachment_records
    )
    if not permitted:
        abort(404)

    safe_name = secure_filename(stored_name)
    file_path = (ENQUIRY_UPLOAD_FOLDER / safe_name).resolve()
    upload_root = ENQUIRY_UPLOAD_FOLDER.resolve()
    if file_path.parent != upload_root or not file_path.is_file():
        abort(404)

    original_name = next(
        item["original_name"]
        for item in attachment_records
        if item["stored_name"] == stored_name
    )
    from flask import send_from_directory
    response = send_from_directory(
        str(upload_root),
        safe_name,
        as_attachment=True,
        download_name=original_name,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route(
    "/api/enquiry/<int:enquiry_id>/status",
    methods=["POST"],
)
@admin_required
def update_enquiry_status(enquiry_id):
    """Update an enquiry status for an authenticated administrator."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request."}), 400

    status = data.get("status")

    if not isinstance(status, str) or status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid enquiry status."}), 400

    try:
        if not ENQUIRIES_FILE.exists():
            return jsonify({
                "error": "No enquiries have been saved yet."
            }), 404

        # Add the status column and preserve all existing enquiries.
        ensure_enquiries_schema()

        with ENQUIRIES_FILE.open(
            "r", newline="", encoding="utf-8"
        ) as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        if enquiry_id < 0 or enquiry_id >= len(rows):
            return jsonify({"error": "Enquiry not found."}), 404

        rows[enquiry_id]["status"] = status
        temporary_file = ENQUIRIES_FILE.with_suffix(".csv.tmp")

        with temporary_file.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()

            for row in rows:
                writer.writerow({
                    field: row.get(field, "")
                    for field in fieldnames
                })

        temporary_file.replace(ENQUIRIES_FILE)

        return jsonify({
            "message": "Enquiry status updated.",
            "status": status,
        })

    except (OSError, csv.Error):
        app.logger.exception("Could not update enquiry status")
        return jsonify({
            "error": "Could not save the status. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )