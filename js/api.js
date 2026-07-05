// ── WorkingEveryday API ─────────────────────────────────────────────────────
const API = "https://workingeveryday.onrender.com";

async function apiCall(method, path, body) {
  const opts = {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" }
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  return res.json();
}

// ── auth ───────────────────────────────────────────────────────────────────
const api = {
  signup:  (username, password) => apiCall("POST", "/api/signup",  { username, password }),
  login:   (username, password) => apiCall("POST", "/api/login",   { username, password }),
  logout:  ()                   => apiCall("POST", "/api/logout"),
  me:      ()                   => apiCall("GET",  "/api/me"),

  // workspaces
  getWorkspaces:    ()           => apiCall("GET",  "/api/workspaces"),
  createWorkspace:  (name)       => apiCall("POST", "/api/workspaces",       { name }),
  joinWorkspace:    (code)       => apiCall("POST", "/api/workspaces/join",  { invite_code: code }),

  // tasks
  getTasks:   (workspace_id)         => apiCall("GET",   "/api/tasks" + (workspace_id ? "?workspace_id="+workspace_id : "")),
  createTask: (title, workspace_id)  => apiCall("POST",  "/api/tasks",        { title, workspace_id }),
  moveTask:   (id, status)           => apiCall("PATCH",  "/api/tasks/"+id,   { status }),
  deleteTask: (id)                   => apiCall("DELETE", "/api/tasks/"+id),

  // notes
  getNotes:   ()                     => apiCall("GET",   "/api/notes"),
  createNote: (title, body)          => apiCall("POST",  "/api/notes",        { title, body }),
  updateNote: (id, title, body)      => apiCall("PATCH",  "/api/notes/"+id,   { title, body }),
  deleteNote: (id)                   => apiCall("DELETE", "/api/notes/"+id),

  // events
  getEvents:   (workspace_id)        => apiCall("GET",   "/api/events" + (workspace_id ? "?workspace_id="+workspace_id : "")),
  createEvent: (title, event_date, event_time, workspace_id) =>
                                        apiCall("POST",  "/api/events",       { title, event_date, event_time, workspace_id }),
  deleteEvent: (id)                  => apiCall("DELETE", "/api/events/"+id),

  // files
  getFiles:   (workspace_id)         => apiCall("GET",   "/api/files" + (workspace_id ? "?workspace_id="+workspace_id : "")),
  createFile: (name, size, path, workspace_id) =>
                                        apiCall("POST",  "/api/files",        { name, size, path, workspace_id }),
  deleteFile: (id)                   => apiCall("DELETE", "/api/files/"+id),
};
