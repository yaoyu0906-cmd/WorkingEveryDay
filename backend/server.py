import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from supabase import create_client

# ── setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "alvin3301")

CORS(app, supports_credentials=True, origins=[
    "https://workingeveryday.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:5500"
])

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── helpers ────────────────────────────────────────────────────────────────
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    res = db.table("users").select("*").eq("id", uid).single().execute()
    return res.data

def require_login():
    u = current_user()
    if not u:
        return jsonify({"error": "Not logged in"}), 401
    return u

# ── auth ───────────────────────────────────────────────────────────────────
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # check if username taken
    existing = db.table("users").select("id").eq("username", username).execute()
    if existing.data:
        return jsonify({"error": "Username already taken"}), 409

    user = db.table("users").insert({
        "username": username,
        "password": password
    }).execute()

    u = user.data[0]
    session["user_id"] = u["id"]
    return jsonify({"ok": True, "user": {"id": u["id"], "username": u["username"]}}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    res = db.table("users").select("*").eq("username", username).eq("password", password).execute()
    if not res.data:
        return jsonify({"error": "Invalid username or password"}), 401

    u = res.data[0]
    session["user_id"] = u["id"]
    return jsonify({"ok": True, "user": {"id": u["id"], "username": u["username"]}})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me", methods=["GET"])
def me():
    u = current_user()
    if not u:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify({"id": u["id"], "username": u["username"]})


# ── workspaces ─────────────────────────────────────────────────────────────
@app.route("/api/workspaces", methods=["GET"])
def get_workspaces():
    u = require_login()
    if isinstance(u, tuple): return u

    # get all workspace_ids this user is a member of
    members = db.table("workspace_members").select("workspace_id").eq("user_id", u["id"]).execute()
    ids = [m["workspace_id"] for m in members.data]
    if not ids:
        return jsonify([])

    workspaces = db.table("workspaces").select("*").in_("id", ids).execute()
    return jsonify(workspaces.data)


@app.route("/api/workspaces", methods=["POST"])
def create_workspace():
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400

    slug = name.lower().replace(" ", "")

    # check slug taken
    existing = db.table("workspaces").select("id").eq("slug", slug).execute()
    if existing.data:
        return jsonify({"error": "Workspace name already taken"}), 409

    ws = db.table("workspaces").insert({
        "name": name,
        "slug": slug,
        "owner_id": u["id"]
    }).execute().data[0]

    # add creator as owner
    db.table("workspace_members").insert({
        "workspace_id": ws["id"],
        "user_id": u["id"],
        "role": "owner"
    }).execute()

    return jsonify(ws), 201


@app.route("/api/workspaces/join", methods=["POST"])
def join_workspace():
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    code = data.get("invite_code", "").strip()

    ws = db.table("workspaces").select("*").eq("invite_code", code).execute()
    if not ws.data:
        return jsonify({"error": "Invalid invite code"}), 404

    ws = ws.data[0]

    # already a member?
    existing = db.table("workspace_members") \
        .select("id").eq("workspace_id", ws["id"]).eq("user_id", u["id"]).execute()
    if existing.data:
        return jsonify({"error": "Already a member"}), 409

    db.table("workspace_members").insert({
        "workspace_id": ws["id"],
        "user_id": u["id"],
        "role": "member"
    }).execute()

    return jsonify({"ok": True, "workspace": ws})


# ── tasks ──────────────────────────────────────────────────────────────────
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    u = require_login()
    if isinstance(u, tuple): return u

    workspace_id = request.args.get("workspace_id")
    if workspace_id:
        tasks = db.table("tasks").select("*").eq("workspace_id", workspace_id).execute()
    else:
        # personal = no workspace, just this user
        tasks = db.table("tasks").select("*").eq("user_id", u["id"]).is_("workspace_id", "null").execute()

    return jsonify(tasks.data)


@app.route("/api/tasks", methods=["POST"])
def create_task():
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    task = db.table("tasks").insert({
        "user_id": u["id"],
        "workspace_id": data.get("workspace_id"),
        "title": data.get("title", "").strip(),
        "status": data.get("status", "todo")
    }).execute()

    return jsonify(task.data[0]), 201


@app.route("/api/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    task = db.table("tasks").update({"status": data.get("status")}).eq("id", task_id).execute()
    return jsonify(task.data[0])


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    u = require_login()
    if isinstance(u, tuple): return u

    db.table("tasks").delete().eq("id", task_id).execute()
    return jsonify({"ok": True})


# ── notes ──────────────────────────────────────────────────────────────────
@app.route("/api/notes", methods=["GET"])
def get_notes():
    u = require_login()
    if isinstance(u, tuple): return u

    notes = db.table("notes").select("*").eq("user_id", u["id"]).order("updated_at", desc=True).execute()
    return jsonify(notes.data)


@app.route("/api/notes", methods=["POST"])
def create_note():
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    note = db.table("notes").insert({
        "user_id": u["id"],
        "title": data.get("title", ""),
        "body": data.get("body", "")
    }).execute()

    return jsonify(note.data[0]), 201


@app.route("/api/notes/<note_id>", methods=["PATCH"])
def update_note(note_id):
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    note = db.table("notes").update({
        "title": data.get("title", ""),
        "body": data.get("body", ""),
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", note_id).eq("user_id", u["id"]).execute()

    return jsonify(note.data[0])


@app.route("/api/notes/<note_id>", methods=["DELETE"])
def delete_note(note_id):
    u = require_login()
    if isinstance(u, tuple): return u

    db.table("notes").delete().eq("id", note_id).eq("user_id", u["id"]).execute()
    return jsonify({"ok": True})


# ── events (calendar) ──────────────────────────────────────────────────────
@app.route("/api/events", methods=["GET"])
def get_events():
    u = require_login()
    if isinstance(u, tuple): return u

    workspace_id = request.args.get("workspace_id")
    if workspace_id:
        events = db.table("events").select("*").eq("workspace_id", workspace_id).execute()
    else:
        events = db.table("events").select("*").eq("user_id", u["id"]).is_("workspace_id", "null").execute()

    return jsonify(events.data)


@app.route("/api/events", methods=["POST"])
def create_event():
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    event = db.table("events").insert({
        "user_id": u["id"],
        "workspace_id": data.get("workspace_id"),
        "title": data.get("title", "").strip(),
        "event_date": data.get("event_date"),
        "event_time": data.get("event_time", "")
    }).execute()

    return jsonify(event.data[0]), 201


@app.route("/api/events/<event_id>", methods=["DELETE"])
def delete_event(event_id):
    u = require_login()
    if isinstance(u, tuple): return u

    db.table("events").delete().eq("id", event_id).execute()
    return jsonify({"ok": True})


# ── files (metadata) ───────────────────────────────────────────────────────
@app.route("/api/files", methods=["GET"])
def get_files():
    u = require_login()
    if isinstance(u, tuple): return u

    workspace_id = request.args.get("workspace_id")
    if workspace_id:
        files = db.table("files").select("*").eq("workspace_id", workspace_id).execute()
    else:
        files = db.table("files").select("*").eq("user_id", u["id"]).is_("workspace_id", "null").execute()

    return jsonify(files.data)


@app.route("/api/files", methods=["POST"])
def create_file():
    u = require_login()
    if isinstance(u, tuple): return u

    data = request.json
    f = db.table("files").insert({
        "user_id": u["id"],
        "workspace_id": data.get("workspace_id"),
        "name": data.get("name", ""),
        "size": data.get("size", 0),
        "path": data.get("path", "")
    }).execute()

    return jsonify(f.data[0]), 201


@app.route("/api/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    u = require_login()
    if isinstance(u, tuple): return u

    db.table("files").delete().eq("id", file_id).execute()
    return jsonify({"ok": True})


# ── run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
