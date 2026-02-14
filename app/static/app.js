(function () {
  const apis = window.TUNEDUP?.apis || { artists: "/api/artists", albums: "/api/albums", songs: "/api/songs" };
  const types = ["artists", "albums", "songs"];
  const nameKeys = { artists: "artist_name", albums: "album_name", songs: "song_name" };

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : null;
  }

  async function api(type, method, path, body) {
    const base = apis[type] || "/api/artists";
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const token = getCsrfToken();
    if (token) opts.headers["X-CSRFToken"] = token;
    const res = await fetch(base + path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  const panels = types.map((t) => ({
    type: t,
    panelEl: document.getElementById("panel-" + t),
    listEl: document.getElementById("ranking-items-" + t),
    containerEl: document.getElementById("rankings-list-" + t),
    inputEl: document.getElementById(t.slice(0, -1) + "-input"),
    addBtn: document.getElementById("add-" + t.slice(0, -1) + "-btn"),
  }));

  const sidebarLinks = document.querySelectorAll(".sidebar-link");
  let currentType = "artists";
  let draggedEl = null;

  if (!panels[0].listEl || !panels[0].containerEl) return;

  function setEmpty(type, empty) {
    const p = panels.find((x) => x.type === type);
    if (p && p.containerEl) p.containerEl.setAttribute("data-empty", empty ? "true" : "false");
  }

  function getListEl(type) {
    return panels.find((x) => x.type === type)?.listEl;
  }

  function renderItem(type, item) {
    const nameKey = nameKeys[type];
    const name = item[nameKey];
    const li = document.createElement("li");
    li.className = "ranking-item";
    li.dataset.id = item.id;
    li.dataset.type = type;
    li.draggable = true;
    li.innerHTML =
      '<span class="drag-handle" aria-hidden="true">⋮⋮</span>' +
      '<span class="rank-num">' + item.rank_position + "</span>" +
      '<span class="item-name">' + escapeHtml(name) + "</span>" +
      '<button type="button" class="remove-btn" aria-label="Remove">×</button>';
    li.querySelector(".remove-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      removeItem(type, item.id);
    });
    li.addEventListener("dragstart", onDragStart);
    li.addEventListener("dragend", onDragEnd);
    li.addEventListener("dragover", onDragOver);
    li.addEventListener("drop", onDrop);
    return li;
  }

  function syncRanks(type) {
    const listEl = getListEl(type);
    if (!listEl) return;
    listEl.querySelectorAll(".ranking-item").forEach((el, i) => {
      el.querySelector(".rank-num").textContent = i + 1;
    });
  }

  async function loadRankings(type) {
    const p = panels.find((x) => x.type === type);
    if (!p || !p.listEl) return;
    try {
      const data = await api(type, "GET", "/");
      p.listEl.innerHTML = "";
      data.forEach((item) => p.listEl.appendChild(renderItem(type, item)));
      setEmpty(type, data.length === 0);
    } catch (e) {
      if (e.message === "Unauthorized" || String(e.message).includes("401")) {
        window.location.href = "/auth/login?next=" + encodeURIComponent(window.location.pathname);
      }
    }
  }

  async function addItem(type) {
    const p = panels.find((x) => x.type === type);
    if (!p || !p.inputEl || !p.addBtn) return;
    const nameKey = nameKeys[type];
    const name = (p.inputEl.value || "").trim();
    if (!name) return;
    p.addBtn.disabled = true;
    try {
      const payload = {};
      payload[nameKey] = name;
      const item = await api(type, "POST", "/", payload);
      p.listEl.appendChild(renderItem(type, item));
      setEmpty(type, false);
      syncRanks(type);
      p.inputEl.value = "";
    } catch (e) {
      alert(e.message || "Could not add");
    } finally {
      p.addBtn.disabled = false;
    }
  }

  async function removeItem(type, id) {
    const p = panels.find((x) => x.type === type);
    if (!p) return;
    try {
      await api(type, "DELETE", "/" + id);
      const el = p.listEl.querySelector('[data-id="' + id + '"]');
      if (el) el.remove();
      syncRanks(type);
      setEmpty(type, p.listEl.children.length === 0);
    } catch (e) {
      alert(e.message || "Could not remove");
    }
  }

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
    if (li === draggedEl || !draggedEl || li.dataset.type !== draggedEl.dataset.type) return;
    const listEl = getListEl(li.dataset.type);
    if (!listEl) return;
    const all = Array.from(listEl.querySelectorAll(".ranking-item"));
    const from = all.indexOf(draggedEl);
    const to = all.indexOf(li);
    if (from === -1 || to === -1) return;
    if (from < to) listEl.insertBefore(draggedEl, li.nextSibling);
    else listEl.insertBefore(draggedEl, li);
    syncRanks(li.dataset.type);
  }

  function onDrop(e) {
    e.preventDefault();
    if (!draggedEl) return;
    const type = draggedEl.dataset.type;
    const listEl = getListEl(type);
    if (!listEl) return;
    const order = Array.from(listEl.querySelectorAll(".ranking-item")).map((el) => parseInt(el.dataset.id, 10));
    api(type, "PUT", "/reorder", { order }).then(() => syncRanks(type)).catch(() => loadRankings(type));
  }

  function switchPanel(type) {
    currentType = type;
    panels.forEach((p) => {
      if (p.panelEl) p.panelEl.classList.toggle("active", p.type === type);
    });
    sidebarLinks.forEach((link) => {
      link.classList.toggle("active", link.dataset.panel === type);
    });
    loadRankings(type);
  }

  sidebarLinks.forEach((link) => {
    link.addEventListener("click", () => switchPanel(link.dataset.panel));
  });

  const layoutEl = document.getElementById("dashboard-layout");
  const toggleBtn = document.getElementById("sidebar-toggle");
  if (layoutEl && toggleBtn) {
    toggleBtn.addEventListener("click", () => layoutEl.classList.toggle("sidebar-collapsed"));
  }

  panels.forEach((p) => {
    if (p.addBtn && p.inputEl) {
      p.addBtn.addEventListener("click", () => addItem(p.type));
      p.inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter") addItem(p.type);
      });
    }
  });

  switchPanel("artists");

  // ——— Spotify (deferred so page paints first; short timeout so status never blocks) ———
  const spotifyBase = window.TUNEDUP?.spotify;
  if (spotifyBase) {
    const statusEl = document.getElementById("spotify-status");
    const connectBtn = document.getElementById("spotify-connect-btn");
    const setSpotifyUI = (connected) => {
      if (statusEl) statusEl.textContent = connected ? "Spotify connected" : "Connect for recommendations";
      if (connectBtn) connectBtn.style.display = connected ? "none" : "block";
      ["recommendations-block", "recommendations-block-artists", "recommendations-block-albums"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.style.display = connected ? "block" : "none";
      });
    };
    setTimeout(() => {
      const c = new AbortController();
      const t = setTimeout(() => c.abort(), 5000);
      fetch(spotifyBase.status, { credentials: "same-origin", signal: c.signal })
        .then((r) => r.json())
        .then((data) => { setSpotifyUI(!!data.connected); })
        .catch(() => {
          if (statusEl) statusEl.textContent = "Connect for recommendations";
          setSpotifyUI(false);
        })
        .finally(() => clearTimeout(t));
    }, 0);
  }

  function debounce(fn, ms) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  function setupSuggest(inputId, dropdownId, type) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown || !spotifyBase) return;
    let abort = null;
    const doSearch = debounce(async () => {
      const q = input.value.trim();
      if (q.length < 2) {
        dropdown.classList.remove("open");
        dropdown.innerHTML = "";
        return;
      }
      if (abort) abort.abort();
      abort = new AbortController();
      try {
        const res = await fetch(
          spotifyBase.suggest + "?q=" + encodeURIComponent(q) + "&type=" + (type === "artist" ? "artist" : "track") + "&limit=8",
          { credentials: "same-origin", signal: abort.signal }
        );
        const data = await res.json();
        if (!Array.isArray(data)) return;
        dropdown.innerHTML = "";
        if (data.length === 0) {
          dropdown.classList.remove("open");
          return;
        }
        data.forEach((item) => {
          const div = document.createElement("div");
          div.className = "suggest-item";
          div.setAttribute("role", "option");
          if (item.type === "artist") {
            div.textContent = item.name;
            div.dataset.name = item.name;
          } else {
            div.innerHTML = item.name + (item.artist ? ' <span class="suggest-artist">' + escapeHtml(item.artist) + "</span>" : "");
            div.dataset.name = item.name + (item.artist ? " – " + item.artist : "");
          }
          div.addEventListener("click", () => {
            input.value = item.type === "artist" ? item.name : item.name + " – " + (item.artist || "");
            dropdown.classList.remove("open");
            dropdown.innerHTML = "";
          });
          dropdown.appendChild(div);
        });
        dropdown.classList.add("open");
      } catch (e) {
        if (e.name !== "AbortError") dropdown.classList.remove("open");
      }
    }, 300);
    input.addEventListener("input", doSearch);
    input.addEventListener("focus", () => {
      if (dropdown.children.length) dropdown.classList.add("open");
    });
    document.addEventListener("click", (e) => {
      if (!dropdown.contains(e.target) && e.target !== input) dropdown.classList.remove("open");
    });
  }
  setupSuggest("artist-input", "suggest-artist", "artist");
  setupSuggest("song-input", "suggest-song", "track");

  function fetchWithTimeout(url, ms) {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), ms);
    return fetch(url, { credentials: "same-origin", signal: c.signal }).finally(() => clearTimeout(t));
  }

  const fetchRecBtn = document.getElementById("fetch-recommendations-btn");
  const recList = document.getElementById("recommendations-list");
  if (spotifyBase && fetchRecBtn && recList) {
    fetchRecBtn.addEventListener("click", async () => {
      fetchRecBtn.disabled = true;
      fetchRecBtn.textContent = "Loading…";
      try {
        const res = await fetchWithTimeout(spotifyBase.recommendations, 35000);
        const data = await res.json();
        recList.innerHTML = "";
        if (data.tracks && data.tracks.length) {
          data.tracks.forEach((t) => {
            const name = t.artist ? t.name + " – " + t.artist : t.name;
            const li = document.createElement("li");
            li.innerHTML = '<span>' + escapeHtml(t.name) + (t.artist ? ' <span class="suggest-artist">' + escapeHtml(t.artist) + "</span>" : "") + '</span><button type="button" class="btn btn-ghost rec-add">Add</button>';
            li.querySelector(".rec-add").addEventListener("click", () => {
              const songInput = document.getElementById("song-input");
              const songPanel = panels.find((p) => p.type === "songs");
              if (songInput && songPanel) {
                songInput.value = name;
                addItem("songs");
              }
            });
            recList.appendChild(li);
          });
        } else {
          recList.innerHTML = "<li>" + (data.message || data.error || "No recommendations right now.") + "</li>";
        }
      } catch (e) {
        recList.innerHTML = "<li>" + (e.name === "AbortError" ? "Request timed out. Check your connection or try again in a moment. If it keeps happening, disconnect and reconnect Spotify in the sidebar." : "Could not load recommendations.") + "</li>";
      } finally {
        fetchRecBtn.disabled = false;
        fetchRecBtn.textContent = "Load recommended songs";
      }
    });
  }

  const fetchArtistsBtn = document.getElementById("fetch-recommendations-artists-btn");
  const recListArtists = document.getElementById("recommendations-list-artists");
  if (spotifyBase && fetchArtistsBtn && recListArtists) {
    fetchArtistsBtn.addEventListener("click", async () => {
      fetchArtistsBtn.disabled = true;
      fetchArtistsBtn.textContent = "Loading…";
      try {
        const res = await fetchWithTimeout(spotifyBase.recommendationsArtists, 35000);
        const data = await res.json();
        recListArtists.innerHTML = "";
        if (data.artists && data.artists.length) {
          data.artists.forEach((a) => {
            const li = document.createElement("li");
            li.innerHTML = '<span>' + escapeHtml(a.name) + '</span><button type="button" class="btn btn-ghost rec-add">Add</button>';
            li.querySelector(".rec-add").addEventListener("click", () => {
              const artistInput = document.getElementById("artist-input");
              const artistPanel = panels.find((p) => p.type === "artists");
              if (artistInput && artistPanel) {
                artistInput.value = a.name;
                addItem("artists");
              }
            });
            recListArtists.appendChild(li);
          });
        } else {
          recListArtists.innerHTML = "<li>" + (data.error || "No top artists. Listen to more on Spotify.") + "</li>";
        }
      } catch (e) {
        recListArtists.innerHTML = "<li>" + (e.name === "AbortError" ? "Request timed out. Check your connection or try again. If it keeps happening, reconnect Spotify from the sidebar." : "Could not load artists.") + "</li>";
      } finally {
        fetchArtistsBtn.disabled = false;
        fetchArtistsBtn.textContent = "Load my top artists";
      }
    });
  }

  const fetchAlbumsBtn = document.getElementById("fetch-recommendations-albums-btn");
  const recListAlbums = document.getElementById("recommendations-list-albums");
  if (spotifyBase && fetchAlbumsBtn && recListAlbums) {
    fetchAlbumsBtn.addEventListener("click", async () => {
      fetchAlbumsBtn.disabled = true;
      fetchAlbumsBtn.textContent = "Loading…";
      try {
        const res = await fetchWithTimeout(spotifyBase.recommendationsAlbums, 35000);
        const data = await res.json();
        recListAlbums.innerHTML = "";
        if (data.albums && data.albums.length) {
          data.albums.forEach((a) => {
            const name = a.artist ? a.name + " – " + a.artist : a.name;
            const li = document.createElement("li");
            li.innerHTML = '<span>' + escapeHtml(a.name) + (a.artist ? ' <span class="suggest-artist">' + escapeHtml(a.artist) + "</span>" : "") + '</span><button type="button" class="btn btn-ghost rec-add">Add</button>';
            li.querySelector(".rec-add").addEventListener("click", () => {
              const albumInput = document.getElementById("album-input");
              const albumPanel = panels.find((p) => p.type === "albums");
              if (albumInput && albumPanel) {
                albumInput.value = a.artist ? a.name + " – " + a.artist : a.name;
                addItem("albums");
              }
            });
            recListAlbums.appendChild(li);
          });
        } else {
          recListAlbums.innerHTML = "<li>" + (data.error || "No albums. Listen to more on Spotify.") + "</li>";
        }
      } catch (e) {
        recListAlbums.innerHTML = "<li>" + (e.name === "AbortError" ? "Request timed out. Check your connection or try again. If it keeps happening, reconnect Spotify from the sidebar." : "Could not load albums.") + "</li>";
      } finally {
        fetchAlbumsBtn.disabled = false;
        fetchAlbumsBtn.textContent = "Load albums from my listening";
      }
    });
  }
})();
