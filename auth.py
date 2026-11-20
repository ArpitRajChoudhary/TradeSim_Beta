import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SESSION_SECRET = os.getenv("SESSION_SECRET")

DATABASE_PATH = BASE_DIR / "tradesim_users.db"

SESSION_COOKIE_NAME = "tradesim_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_sub TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                name TEXT NOT NULL,
                picture TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT NOT NULL
            )
        """)

        connection.commit()


# --------------------------------------------------
# GOOGLE TOKEN VERIFICATION
# --------------------------------------------------

def verify_google_token(token: str):

    if not GOOGLE_CLIENT_ID:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is not configured."
        )

    try:
        payload = id_token.verify_oauth2_token(
            token,
            Request(),
            GOOGLE_CLIENT_ID,
        )

    except ValueError as error:
        raise ValueError(
            "Invalid or expired Google sign-in token."
        ) from error

    google_sub = payload.get("sub")
    email = payload.get("email")
    email_verified = payload.get("email_verified", False)

    if not google_sub or not email:
        raise ValueError(
            "Google account information is incomplete."
        )

    if email_verified is not True:
        raise ValueError(
            "Please use a verified Google email address."
        )

    return {
        "google_sub": google_sub,
        "email": email,
        "name": payload.get("name") or email.split("@")[0],
        "picture": payload.get("picture"),
    }


# --------------------------------------------------
# USER MANAGEMENT
# --------------------------------------------------

def get_or_create_user(google_user):

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    initialize_database()

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO users (
                google_sub,
                email,
                name,
                picture,
                created_at,
                last_login
            )
            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(google_sub)
            DO UPDATE SET
                email = excluded.email,
                name = excluded.name,
                picture = excluded.picture,
                last_login = excluded.last_login
        """, (
            google_user["google_sub"],
            google_user["email"],
            google_user["name"],
            google_user.get("picture"),
            now,
            now,
        ))

        connection.commit()

        row = connection.execute("""
            SELECT id, email, name, picture, created_at
            FROM users
            WHERE google_sub = ?
        """, (
            google_user["google_sub"],
        )).fetchone()

    return dict(row)


def get_user_by_id(user_id):

    initialize_database()

    with get_connection() as connection:

        row = connection.execute("""
            SELECT id, email, name, picture, created_at
            FROM users
            WHERE id = ?
        """, (
            user_id,
        )).fetchone()

    return dict(row) if row else None


# --------------------------------------------------
# APPLICATION SESSION
# --------------------------------------------------

def get_session_serializer():

    if not SESSION_SECRET:
        raise RuntimeError(
            "SESSION_SECRET is not configured."
        )

    return URLSafeTimedSerializer(
        SESSION_SECRET,
        salt="tradesim-auth-session",
    )


def create_session_token(user_id):

    serializer = get_session_serializer()

    return serializer.dumps({
        "user_id": user_id,
    })


def verify_session_token(token):

    serializer = get_session_serializer()

    try:
        data = serializer.loads(
            token,
            max_age=SESSION_MAX_AGE,
        )

        user_id = data.get("user_id")

        if not isinstance(user_id, int):
            return None

        return get_user_by_id(user_id)

    except (BadSignature, SignatureExpired):
        return None
