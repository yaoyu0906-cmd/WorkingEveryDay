// ── WorkingEveryday Main ────────────────────────────────────────────────────

function getUsername() {
  return sessionStorage.getItem("wed_username") || "User";
}

// run on main.html to load real workspaces from backend
async function loadWorkspaces() {
  const user = await requireAuth();
  if (!user) return;

  const greet = document.getElementById("greeting");
  if (greet) greet.textContent = "Hey, " + user.username;

  const res = await api.getWorkspaces();
  if (res.error || !Array.isArray(res)) return;

  const grid = document.getElementById("workspace-grid");
  if (!grid) return;

  // clear company cards (keep personal + add)
  const personal = grid.querySelector(".card-personal");
  const addCard   = grid.querySelector(".card-add");
  grid.innerHTML = "";
  if (personal) grid.appendChild(personal);

  res.forEach(function(ws) {
    const card = document.createElement("div");
    card.className = "card card-block";
    card.innerHTML =
      '<div class="card-icon">🏢</div>' +
      '<div class="card-tag">Company</div>' +
      '<div class="card-title">' + ws.name + '</div>' +
      '<div class="card-desc">Team chat, shared files & announcements</div>' +
      '<button class="btn-full" onclick="location.href=\'/' + ws.slug + '\'">Open</button>';
    grid.insertBefore(card, addCard);
  });
}
