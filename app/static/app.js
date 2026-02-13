(function () {
  const apiBase = window.TUNEDUP?.apiBase || "/api/artists";

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : null;
  }

  async function api(method, path, body) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const token = getCsrfToken();
    if (token) opts.headers["X-CSRFToken"] = token;
    const res = await fetch(apiBase + path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }

  const listEl = document.getElementById("ranking-items");
  const containerEl = document.getElementById("rankings-list");
  const emptyEl = document.getElementById("empty-state");
  const inputEl = document.getElementById("artist-input");
  const addBtn = document.getElementById("add-artist-btn");

  if (!listEl || !containerEl) return;

  function setEmpty(empty) {
    containerEl.setAttribute("data-empty", empty ? "true" : "false");
  }

  function renderItem(item) {
    const li = document.createElement("li");
    li.className = "ranking-item";
    li.dataset.id = item.id;
    li.draggable = true;
    li.innerHTML =
      '<span class="drag-handle" aria-hidden="true">⋮⋮</span>' +
      '<span class="rank-num">' + item.rank_position + "</span>" +
      '<span class="artist-name">' + escapeHtml(item.artist_name) + "</span>" +
      '<button type="button" class="remove-btn" aria-label="Remove">×</button>';
    const removeBtn = li.querySelector(".remove-btn");
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      removeArtist(item.id);
    });
    li.addEventListener("dragstart", onDragStart);
    li.addEventListener("dragend", onDragEnd);
    li.addEventListener("dragover", onDragOver);
    li.addEventListener("drop", onDrop);
    return li;
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function syncRanks() {
    const items = listEl.querySelectorAll(".ranking-item");
    items.forEach((el, i) => {
      el.querySelector(".rank-num").textContent = i + 1;
    });
  }

  async function loadRankings() {
    try {
      const data = await api("GET", "/");
      listEl.innerHTML = "";
      data.forEach((item) => listEl.appendChild(renderItem(item)));
      setEmpty(data.length === 0);
    } catch (e) {
      if (e.message === "Unauthorized" || e.message.includes("401")) {
        window.location.href = "/auth/login?next=" + encodeURIComponent(window.location.pathname);
      }
    }
  }

  async function addArtist() {
    const name = (inputEl && inputEl.value || "").trim();
    if (!name) return;
    addBtn.disabled = true;
    try {
      const item = await api("POST", "/", { artist_name: name });
      listEl.appendChild(renderItem(item));
      setEmpty(false);
      syncRanks();
      if (inputEl) inputEl.value = "";
    } catch (e) {
      alert(e.message || "Could not add artist");
    } finally {
      addBtn.disabled = false;
    }
  }

  async function removeArtist(id) {
    try {
      await api("DELETE", "/" + id);
      const el = listEl.querySelector('[data-id="' + id + '"]');
      if (el) el.remove();
      syncRanks();
      setEmpty(listEl.children.length === 0);
    } catch (e) {
      alert(e.message || "Could not remove");
    }
  }

  let draggedEl = null;

  function onDragStart(e) {
    draggedEl = e.currentTarget;
    e.currentTarget.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", e.currentTarget.dataset.id);
  }

  function onDragEnd(e) {
    e.currentTarget.classList.remove("dragging");
    draggedEl = null;
  }

  function onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    const li = e.currentTarget;
    if (li !== draggedEl && draggedEl) {
      const all = Array.from(listEl.querySelectorAll(".ranking-item"));
      const from = all.indexOf(draggedEl);
      const to = all.indexOf(li);
      if (from < to) li.parentNode.insertBefore(draggedEl, li.nextSibling);
      else li.parentNode.insertBefore(draggedEl, li);
      syncRanks();
    }
  }

  function onDrop(e) {
    e.preventDefault();
    if (!draggedEl) return;
    const order = Array.from(listEl.querySelectorAll(".ranking-item")).map((el) => parseInt(el.dataset.id, 10));
    api("PUT", "/reorder", { order }).then(syncRanks).catch(() => loadRankings());
  }

  if (addBtn && inputEl) {
    addBtn.addEventListener("click", addArtist);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") addArtist();
    });
  }

  loadRankings();
})();
