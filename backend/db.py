# 登录 / 注册（账号存取）由 deepseek v4 pro 生成。
import datetime
import hashlib
import os
import secrets

import pymysql

DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "9275"),
    "database": os.environ.get("MYSQL_DATABASE", "jigou"),
    "charset": "utf8mb4",
}

DB_NAME = DB_CONFIG["database"]

MAX_QUOTA = 5

_PBKDF2_ITERATIONS = 100_000


def _conn(database=None):
    kwargs = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    kwargs["cursorclass"] = pymysql.cursors.DictCursor
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def _columns(cur, table):
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.columns "
        "WHERE table_schema=%s AND table_name=%s",
        (DB_NAME, table),
    )
    return {row["COLUMN_NAME"] for row in cur.fetchall()}


# 【原创】
def init_db():
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(64) NOT NULL,
                    industry VARCHAR(64) NOT NULL DEFAULT '',
                    quota INT NOT NULL DEFAULT 5,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            existing = _columns(cur, "users")
            if "industry" not in existing:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN industry VARCHAR(64) NOT NULL DEFAULT ''"
                )
            if "quota" not in existing:
                cur.execute("ALTER TABLE users ADD COLUMN quota INT NOT NULL DEFAULT 5")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    token CHAR(64) PRIMARY KEY,
                    username VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS acceptances (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) NOT NULL,
                    doc_hash CHAR(64) NOT NULL,
                    content MEDIUMTEXT NOT NULL,
                    confirm_items TEXT NOT NULL,
                    resolutions TEXT NOT NULL,
                    project_key VARCHAR(64) NOT NULL DEFAULT '',
                    version INT NOT NULL DEFAULT 1,
                    diff TEXT NULL,
                    accepted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            acc_cols = _columns(cur, "acceptances")
            if "project_key" not in acc_cols:
                cur.execute(
                    "ALTER TABLE acceptances ADD COLUMN project_key VARCHAR(64) NOT NULL DEFAULT ''"
                )
            if "version" not in acc_cols:
                cur.execute(
                    "ALTER TABLE acceptances ADD COLUMN version INT NOT NULL DEFAULT 1"
                )
            if "diff" not in acc_cols:
                cur.execute("ALTER TABLE acceptances ADD COLUMN diff TEXT NULL")
        conn.commit()
    finally:
        conn.close()


def hash_password(password: str, salt: str | None = None):
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    ).hex()
    return digest, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    digest, _ = hash_password(password, salt)
    return digest == expected_hash


def user_exists(username: str) -> bool:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username=%s LIMIT 1", (username,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def create_user(username: str, password: str) -> None:
    digest, salt = hash_password(password)
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)",
                (username, digest, salt),
            )
        conn.commit()
    finally:
        conn.close()


def check_login(username: str, password: str) -> bool:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash, salt FROM users WHERE username=%s LIMIT 1",
                (username,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        return False
    return verify_password(password, row["salt"], row["password_hash"])


def get_user(username: str) -> dict | None:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, industry, quota FROM users WHERE username=%s LIMIT 1",
                (username,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def set_industry(username: str, industry: str) -> None:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET industry=%s WHERE username=%s", (industry, username)
            )
        conn.commit()
    finally:
        conn.close()


def set_password(username: str, new_password: str) -> None:
    digest, salt = hash_password(new_password)
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash=%s, salt=%s WHERE username=%s",
                (digest, salt, username),
            )
        conn.commit()
    finally:
        conn.close()


# 【原创】
def get_quota(username: str) -> int:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT quota FROM users WHERE username=%s LIMIT 1", (username,))
            row = cur.fetchone()
    finally:
        conn.close()
    return int(row["quota"]) if row else 0


# 【原创】
def consume_quota(username: str) -> bool:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET quota = quota - 1 WHERE username=%s AND quota > 0",
                (username,),
            )
            conn.commit()
            affected = cur.rowcount
    finally:
        conn.close()
    return affected > 0


# 【原创】
def refund_quota(username: str) -> None:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET quota = LEAST(quota + 1, %s) WHERE username=%s",
                (MAX_QUOTA, username),
            )
        conn.commit()
    finally:
        conn.close()


# 【原创】
def save_acceptance(
    username: str,
    doc_hash: str,
    content: str,
    confirm_items: str,
    resolutions: str,
    project_key: str = "",
    version: int = 1,
    diff: str = "",
):
    accepted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO acceptances "
                "(username, doc_hash, content, confirm_items, resolutions, "
                "project_key, version, diff, accepted_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (username, doc_hash, content, confirm_items, resolutions,
                 project_key, version, diff, accepted_at),
            )
            conn.commit()
            return cur.lastrowid, accepted_at
    finally:
        conn.close()


# 【原创】
def get_latest_acceptance(username: str, project_key: str) -> dict | None:
    if not project_key:
        return None
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM acceptances WHERE username=%s AND project_key=%s "
                "ORDER BY version DESC LIMIT 1",
                (username, project_key),
            )
            return cur.fetchone()
    finally:
        conn.close()


def create_token(username: str) -> str:
    token = secrets.token_hex(32)
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE username=%s", (username,))
            cur.execute(
                "INSERT INTO tokens (token, username) VALUES (%s, %s)", (token, username)
            )
        conn.commit()
    finally:
        conn.close()
    return token


def get_username_by_token(token: str) -> str | None:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM tokens WHERE token=%s LIMIT 1", (token,))
            row = cur.fetchone()
    finally:
        conn.close()
    return row["username"] if row else None


def delete_token(token: str) -> None:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE token=%s", (token,))
        conn.commit()
    finally:
        conn.close()


def delete_account(username: str) -> None:
    conn = _conn(database=DB_NAME)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE username=%s", (username,))
            cur.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
    finally:
        conn.close()
