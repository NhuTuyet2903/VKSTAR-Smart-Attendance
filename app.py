from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = os.environ.get("VKSTAR_SECRET_KEY", "change-this-secret-key-before-deployment")
DB_PATH = Path(__file__).with_name("vkstar.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('employee','supervisor','hr')),
            department TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            work_date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT NOT NULL DEFAULT 'Đúng giờ',
            note TEXT DEFAULT '',
            UNIQUE(user_id, work_date)
        );
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            request_type TEXT NOT NULL,
            request_date TEXT NOT NULL,
            note TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Chờ duyệt',
            created_at TEXT NOT NULL
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            demo_users = [
                ("nv01", "123456", "Nguyễn Thị Mai Anh", "employee", "Mẫu"),
                ("tc01", "123456", "Trần Minh Quân", "supervisor", "Mẫu"),
                ("hr01", "123456", "Lê Hà Phương", "hr", "Nhân sự"),
            ]
            for username, password, name, role, dept in demo_users:
                con.execute(
                    "INSERT INTO users(username,password_hash,full_name,role,department) VALUES(?,?,?,?,?)",
                    (username, generate_password_hash(password), name, role, dept)
                )

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Bạn cần đăng nhập."}), 401
        return fn(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                return jsonify({"error": "Bạn không có quyền thực hiện chức năng này."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "message": "VKSTAR backend đang hoạt động"})

@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE username=? AND active=1", (username,)
        ).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không đúng."}), 401
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]
    session["role"] = user["role"]
    session["department"] = user["department"]
    return jsonify({"message": "Đăng nhập thành công", "user": {
        "id": user["id"], "username": user["username"],
        "name": user["full_name"], "role": user["role"],
        "department": user["department"]
    }})

@app.post("/api/logout")
@login_required
def api_logout():
    session.clear()
    return jsonify({"message": "Đã đăng xuất"})

@app.get("/api/me")
@login_required
def api_me():
    return jsonify({
        "id": session["user_id"], "username": session["username"],
        "name": session["full_name"], "role": session["role"],
        "department": session["department"]
    })

@app.get("/api/staff")
@role_required("supervisor", "hr")
def list_staff():
    with db() as con:
        rows = con.execute(
            "SELECT id,username,full_name,role,department,active FROM users ORDER BY full_name"
        ).fetchall()
    return jsonify([dict(row) for row in rows])

@app.post("/api/staff")
@role_required("hr")
def create_staff():
    data = request.get_json(silent=True) or {}
    required = ["username", "password", "name", "role"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "Vui lòng nhập đủ tên đăng nhập, mật khẩu, họ tên và vai trò."}), 400
    if data["role"] not in ("employee", "supervisor", "hr"):
        return jsonify({"error": "Vai trò không hợp lệ."}), 400
    try:
        with db() as con:
            cur = con.execute(
                """INSERT INTO users(username,password_hash,full_name,role,department)
                   VALUES(?,?,?,?,?)""",
                (data["username"].strip(), generate_password_hash(data["password"]),
                 data["name"].strip(), data["role"], data.get("department", "").strip())
            )
            new_id = cur.lastrowid
        return jsonify({"message": "Đã tạo tài khoản", "id": new_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Tên đăng nhập đã tồn tại."}), 409

@app.get("/api/attendance")
@login_required
def get_attendance():
    with db() as con:
        if session["role"] == "employee":
            rows = con.execute(
                """SELECT a.*,u.full_name,u.department FROM attendance a
                   JOIN users u ON u.id=a.user_id WHERE a.user_id=?
                   ORDER BY work_date DESC""", (session["user_id"],)
            ).fetchall()
        elif session["role"] == "supervisor":
            rows = con.execute(
                """SELECT a.*,u.full_name,u.department FROM attendance a
                   JOIN users u ON u.id=a.user_id
                   WHERE u.department=? ORDER BY work_date DESC""",
                (session["department"],)
            ).fetchall()
        else:
            rows = con.execute(
                """SELECT a.*,u.full_name,u.department FROM attendance a
                   JOIN users u ON u.id=a.user_id ORDER BY work_date DESC"""
            ).fetchall()
    return jsonify([dict(row) for row in rows])

@app.post("/api/attendance")
@role_required("employee")
def mark_attendance():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("check_in", "check_out"):
        return jsonify({"error": "action phải là check_in hoặc check_out."}), 400
    now = datetime.now()
    today = date.today().isoformat()
    clock = now.strftime("%H:%M:%S")
    with db() as con:
        row = con.execute(
            "SELECT * FROM attendance WHERE user_id=? AND work_date=?",
            (session["user_id"], today)
        ).fetchone()
        if action == "check_in":
            if row:
                return jsonify({"error": "Bạn đã chấm công vào hôm nay."}), 409
            # Mốc 08:00 chỉ là mốc demo; điều chỉnh theo ca làm thực tế.
            status = "Đi muộn" if now.hour > 8 or (now.hour == 8 and now.minute > 0) else "Đúng giờ"
            con.execute(
                "INSERT INTO attendance(user_id,work_date,check_in,status) VALUES(?,?,?,?)",
                (session["user_id"], today, clock, status)
            )
            message = "Đã ghi nhận giờ vào."
        else:
            if not row or not row["check_in"]:
                return jsonify({"error": "Bạn chưa chấm công vào."}), 400
            if row["check_out"]:
                return jsonify({"error": "Bạn đã chấm công ra hôm nay."}), 409
            con.execute(
                "UPDATE attendance SET check_out=? WHERE id=?",
                (clock, row["id"])
            )
            message = "Đã ghi nhận giờ ra."
    return jsonify({"message": message, "time": clock, "date": today})

@app.post("/api/requests")
@login_required
def create_request():
    data = request.get_json(silent=True) or {}
    req_type = str(data.get("type", "")).strip()
    req_date = str(data.get("date", "")).strip()
    note = str(data.get("note", "")).strip()
    if not req_type or not req_date or not note:
        return jsonify({"error": "Vui lòng nhập loại đơn, ngày và lý do."}), 400
    with db() as con:
        cur = con.execute(
            """INSERT INTO requests(user_id,request_type,request_date,note,created_at)
               VALUES(?,?,?,?,?)""",
            (session["user_id"], req_type, req_date, note, datetime.now().isoformat(timespec="seconds"))
        )
    return jsonify({"message": "Đã gửi đơn", "id": cur.lastrowid}), 201

@app.get("/api/requests")
@login_required
def list_requests():
    with db() as con:
        if session["role"] == "employee":
            rows = con.execute(
                """SELECT r.*,u.full_name FROM requests r JOIN users u ON u.id=r.user_id
                   WHERE r.user_id=? ORDER BY r.id DESC""", (session["user_id"],)
            ).fetchall()
        elif session["role"] == "supervisor":
            rows = con.execute(
                """SELECT r.*,u.full_name,u.department FROM requests r
                   JOIN users u ON u.id=r.user_id WHERE u.department=?
                   ORDER BY r.id DESC""", (session["department"],)
            ).fetchall()
        else:
            rows = con.execute(
                """SELECT r.*,u.full_name,u.department FROM requests r
                   JOIN users u ON u.id=r.user_id ORDER BY r.id DESC"""
            ).fetchall()
    return jsonify([dict(row) for row in rows])

@app.patch("/api/requests/<int:request_id>")
@role_required("supervisor", "hr")
def update_request(request_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("Đã duyệt", "Từ chối"):
        return jsonify({"error": "Trạng thái không hợp lệ."}), 400
    with db() as con:
        cur = con.execute(
            "UPDATE requests SET status=? WHERE id=?",
            (status, request_id)
        )
    if cur.rowcount == 0:
        return jsonify({"error": "Không tìm thấy đơn."}), 404
    return jsonify({"message": "Đã cập nhật trạng thái đơn."})

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
