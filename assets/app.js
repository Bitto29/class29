const $app = document.getElementById('app');
let lib = { groups: [] }, byId = {}, freq = {};
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = v => { const d = new Date(v); return v && !isNaN(d) ? d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''; };
const pad = n => String(n).padStart(2, '0');
const seenSet = () => { try { return new Set(JSON.parse(localStorage.getItem('c29seen') || '[]')); } catch { return new Set(); } };
const markSeen = id => { try { const s = seenSet(); s.add(id); localStorage.setItem('c29seen', JSON.stringify([...s])); } catch { } };

// Per-device, per-group and per-subject notifications.
const NOTIFY_VERSION = 'c29notif-v2';
const areaKey = (g, t) => NOTIFY_VERSION + ':' + encodeURIComponent(g.name) + ':' + encodeURIComponent(t.name);
function readArea(g, t) {
  try { return JSON.parse(localStorage.getItem(areaKey(g, t)) || 'null'); } catch { return null; }
}
function writeArea(g, t, state) {
  try { localStorage.setItem(areaKey(g, t), JSON.stringify(state)); } catch {}
}
function syncNewClassIds() {
  let legacyKnown = null;
  let legacyUnread = new Set();
  try {
    const raw = localStorage.getItem('c29knownClassIds');
    if (raw !== null) legacyKnown = new Set(JSON.parse(raw));
    legacyUnread = new Set(JSON.parse(localStorage.getItem('c29newClassIds') || '[]'));
  } catch {}
  const allCurrent = [];
  lib.groups.forEach(g => g.topics.forEach(t => {
    const current = t.classes.filter(c => c.video_id).map(c => c.id);
    allCurrent.push(...current);
    let state = readArea(g, t);
    if (!state || state.version !== 2) {
      // Migrate the previous global baseline if available; otherwise quietly baseline this area.
      const known = legacyKnown ? new Set(current.filter(id => legacyKnown.has(id))) : new Set(current);
      const unread = current.filter(id => legacyUnread.has(id) || (legacyKnown && !known.has(id)));
      state = { version: 2, known: [...known], unread };
    } else {
      const known = new Set(state.known || []);
      const unread = new Set(state.unread || []);
      current.forEach(id => { if (!known.has(id)) unread.add(id); });
      state = { version: 2, known: current, unread: [...unread].filter(id => current.includes(id)) };
    }
    writeArea(g, t, state);
  }));
  try { localStorage.setItem('c29knownClassIds', JSON.stringify(allCurrent)); } catch {}
}
const newCount = (g, t) => (readArea(g, t)?.unread || []).length;
function newBadge(count) {
  return count ? `<span class="new-badge" aria-label="${count} new classes">${count > 99 ? '99+' : count}</span>` : '';
}
function acknowledgeSubject(g, t) {
  const state = readArea(g, t);
  if (!state) return;
  state.unread = [];
  writeArea(g, t, state);
}


// Channel banners repeat across hundreds of posts, so they are not real class names.
const isGeneric = t => /PAID COURSE|FREE COURSE|FREE & PAID|FREE MATERIALS|COURSE MATERIALS|\bFCBD\b|\bPCBD\b|ACS FRB|POWERPLAY|\bUDVASH\b|\bINDEX\b|যদি এই ক্লাস|চ্যানেলে যুক্ত|JOIN|SUBSCRIBE/i.test(String(t || '').normalize('NFKC'));
const byTime = (a, b) => (a.date || '').localeCompare(b.date || '') || (a.telegram_message_id - b.telegram_message_id);

function rankGroup(name) {
  const n = String(name || '').toUpperCase();
  const order = ['POWERPLAY 27','ACS FRB 27','POWERPLAY 26','ACS FRB 26'];
  const i = order.findIndex(label => n.includes(label));
  return i < 0 ? order.length : i;
}

function prepare() {
  byId = {}; freq = {};
  lib.groups.forEach(g => g.topics.forEach(t => t.classes.forEach(c => freq[c.title] = (freq[c.title] || 0) + 1)));
  lib.groups.forEach((g, gi) => g.topics.forEach((t, ti) => {
    t.videos = t.classes.filter(c => c.video_id).sort(byTime);
    t.materials = t.classes.filter(c => !c.video_id && (c.resources || []).length && !isGeneric(c.title) || (!c.video_id && /INDEX/i.test(c.title)));
    t.videos.forEach((c, i) => { c.n = i + 1; c.label = isGeneric(c.title) ? 'Class ' + pad(i + 1) : c.title; });
    t.classes.forEach(c => { c.label = c.label || c.title; byId[c.id] = { c, g, t, gi, ti }; });
    t.last = t.videos.length ? t.videos[t.videos.length - 1].date : '';
  }));
}

const crumbs = list => '<nav class="crumbs">' + list.map((x, i) => x[1] ? `<a href="${x[1]}">${esc(x[0])}</a>` : `<span>${esc(x[0])}</span>`).join('<span>›</span>') + '</nav>';

const groupCovers = {
  'PCBD - ( POWERPLAY 27 )': 'https://wntfkemvohfazlckrncj.supabase.co/storage/v1/object/sign/course-thumbnails/ec3d9c6d-6768-4aa0-af63-b2a062ec1dcd.jpg?token=eyJraWQiOiJjZmUyZDg3Yy1iMWYyLTQzYTctOWI3Ni1mYTA2ZmY1ZTAzOWYiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJjb3Vyc2UtdGh1bWJuYWlscy9lYzNkOWM2ZC02NzY4LTRhYTAtYWY2My1iMmEwNjJlYzFkY2QuanBnIiwic2NvcGUiOiJkb3dubG9hZCIsImlhdCI6MTc5MTQ3NzI4NiwiZXhwIjoyMTA2ODM3Mjg2fQ.DwxGDdw6OoDvdgspZwARQ57pFg9-NYGuwGoX86SSqYk',
  'PCBD - ( ACS FRB 27 )': 'https://wntfkemvohfazlckrncj.supabase.co/storage/v1/object/sign/course-thumbnails/56e4c4b3-19a0-43a7-a716-0fd659c69e04.jpg?token=eyJraWQiOiJjZmUyZDg3Yy1iMWYyLTQzYTctOWI3Ni1mYTA2ZmY1ZTAzOWYiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJjb3Vyc2UtdGh1bWJuYWlscy81NmU0YzRiMy0xOWEwLTQzYTctYTcxNi0wZmQ2NTljNjllMDQuanBnIiwic2NvcGUiOiJkb3dubG9hZCIsImlhdCI6MTc5MDQ1NzE3MiwiZXhwIjoyMTA1ODE3MTcyfQ.mzStomWHvbIz0I-a-mdesqRRhwKx-VCVasmxFUL0FP4'
};
function groupCover(g) {
  if (groupCovers[g.name]) return groupCovers[g.name];
  for (const topic of (g.topics || [])) {
    const video = (topic.classes || []).find(c => c.video_id);
    if (video) return 'https://i.ytimg.com/vi/' + encodeURIComponent(video.video_id) + '/hqdefault.jpg';
  }
  return '';
}

function home() {
  const q = ($app.querySelector('#q')?.value || '').trim().toLowerCase();
  const total = lib.groups.reduce((n, g) => n + g.topics.reduce((m, t) => m + t.videos.length, 0), 0);
  $app.innerHTML = `<div class="eyebrow">Your study library</div><h1>Every class.<br><span>One place.</span></h1>
  <p class="sub">${lib.groups.length} groups · ${total} classes</p>
  <input id="q" class="search" type="search" placeholder="Search subject or class…" autocomplete="off" value="${esc(q)}"><div id="out"></div>`;
  const out = $app.querySelector('#out'), input = $app.querySelector('#q');
  const draw = () => {
    const s = input.value.trim().toLowerCase();
    if (!s) {
      out.innerHTML = '<div class="grid">' + lib.groups.map((g, gi) => {
        const v = g.topics.reduce((n, t) => n + t.videos.length, 0);
        const cover = groupCover(g);
        const fresh = g.topics.reduce((n, t) => n + newCount(g, t), 0);
        return `<a class="card" href="#/g/${gi}">${cover ? `<img class="group-cover" src="${esc(cover)}" alt="" loading="lazy" decoding="async">` : `<div class="ico">${esc(g.name.trim().slice(0, 2).toUpperCase())}</div>`}${newBadge(fresh)}<h3>${esc(g.name)}</h3><div class="meta"><span class="pill">${g.topics.length} subjects</span><span class="pill m">${v} classes</span></div></a>`;
      }).join('') + '</div>';
      return;
    }
    const hits = [];
    lib.groups.forEach((g, gi) => g.topics.forEach(t => t.videos.forEach(c => { if ((g.name + ' ' + t.name + ' ' + c.label).toLowerCase().includes(s)) hits.push({ g, t, c }); })));
    out.innerHTML = hits.length ? '<div class="list" style="margin-top:20px">' + hits.slice(0, 80).map(h => row(h.c, h.g.name + ' › ' + h.t.name)).join('') + '</div>' : '<div class="empty">No classes found.</div>';
  };
  input.addEventListener('input', draw); draw();
}

function row(c, sub, on, seen) {
  const thumb = c.video_id ? `<img class="thumb" loading="lazy" alt="" src="https://i.ytimg.com/vi/${encodeURIComponent(c.video_id)}/mqdefault.jpg">` : `<span class="num">↗</span>`;
  const no = c.n ? '#' + pad(c.n) + ' · ' : '';
  return `<a class="item ${on ? 'on' : ''} ${seen && seen.has(c.id) ? 'seen' : ''}" href="#/c/${encodeURIComponent(c.id)}">${thumb}<span class="t"><strong data-video-title-id="${esc(c.video_id || '')}">${esc(c.label)}</strong><small>${esc(no + (sub || fmt(c.date)))}</small></span></a>`;
}

function group(gi) {
  const g = lib.groups[gi]; if (!g) return notFound();
  $app.innerHTML = crumbs([['Home', '#/'], [g.name]]) + `<div class="eyebrow">Group</div><h1 style="font-size:clamp(26px,4vw,40px)">${esc(g.name)}</h1><p class="sub">${g.topics.length} subjects</p>
  <div class="grid">${g.topics.map((t, ti) => `<a class="card" href="#/g/${gi}/t/${ti}"><div class="ico">${esc(t.name.trim().slice(0, 2).toUpperCase())}</div>${newBadge(newCount(g, t))}<h3>${esc(t.name)}</h3><div class="meta"><span class="pill m">${t.videos.length} classes</span>${t.materials.length ? `<span class="pill">${t.materials.length} materials</span>` : ''}${t.last ? `<span class="pill">${fmt(t.last)}</span>` : ''}</div></a>`).join('')}</div>`;
}

function subject(gi, ti) {
  const g = lib.groups[gi], t = g?.topics[ti]; if (!t) return notFound();
  acknowledgeSubject(g, t);
  const seen = seenSet();
  $app.innerHTML = crumbs([['Home', '#/'], [g.name, '#/g/' + gi], [t.name]]) + `<div class="eyebrow">Subject</div><h1 style="font-size:clamp(26px,4vw,40px)">${esc(t.name)}</h1><p class="sub">${t.videos.length} classes</p>
  <div class="list">${t.videos.map(c => row(c, fmt(c.date), false, seen)).join('') || '<div class="empty">No video classes yet.</div>'}</div>
  ${t.materials.length ? '<h2>Materials</h2>' + t.materials.map(m => (m.resources || []).map(r => `<a class="res" target="_blank" rel="noopener noreferrer" href="${esc(r.url)}">↗ ${esc(isGeneric(m.title) ? (r.label || 'Open') : m.title)}</a>`).join('')).join('') : ''}`;
  resolveYouTubeTitles(t.videos);
}

const videoTitleCache = new Map();
async function getYouTubeTitle(videoId) {
  if (!videoId) return '';
  if (videoTitleCache.has(videoId)) return videoTitleCache.get(videoId);
  try {
    const saved = JSON.parse(localStorage.getItem('c29ytTitles') || '{}');
    if (saved[videoId]) {
      videoTitleCache.set(videoId, saved[videoId]);
      return saved[videoId];
    }
  } catch {}
  try {
    const url = 'https://www.youtube.com/oembed?url=' + encodeURIComponent('https://www.youtube.com/watch?v=' + videoId) + '&format=json';
    const response = await fetch(url);
    if (!response.ok) return '';
    const data = await response.json();
    const title = String(data.title || '').trim().slice(0, 180);
    if (title) {
      videoTitleCache.set(videoId, title);
      try {
        const saved = JSON.parse(localStorage.getItem('c29ytTitles') || '{}');
        saved[videoId] = title;
        localStorage.setItem('c29ytTitles', JSON.stringify(saved));
      } catch {}
    }
    return title;
  } catch (error) {
    console.warn('Could not load YouTube title:', videoId, error);
    return '';
  }
}
async function resolveYouTubeTitles(videos) {
  await Promise.all((videos || []).map(async video => {
    if (!video.video_id || !isGeneric(video.title)) return;
    const title = await getYouTubeTitle(video.video_id);
    if (!title) return;
    video.label = title;
    document.querySelectorAll('[data-video-title-id="' + CSS.escape(video.video_id) + '"]').forEach(node => {
      node.textContent = title;
    });
  }));
}

function watch(id) {
  const x = byId[id]; if (!x) return notFound();
  const { c, g, t, gi, ti } = x, i = t.videos.indexOf(c), prev = t.videos[i - 1], next = t.videos[i + 1], seen = seenSet();
  if (c.video_id) markSeen(c.id);
  const link = k => k ? `href="#/c/${encodeURIComponent(k.id)}"` : '';
  $app.innerHTML = crumbs([['Home', '#/'], [g.name, '#/g/' + gi], [t.name, `#/g/${gi}/t/${ti}`], [c.label]]) + `<div class="watch"><div>
  <h1 data-video-title-id="${esc(c.video_id || '')}" style="font-size:clamp(22px,3.5vw,32px);letter-spacing:-.5px">${esc(c.label)}</h1>
  <p class="sub">${esc(t.name)} · ${fmt(c.date)}</p>
  ${c.video_id ? `<div class="player" id="class-player"><iframe title="Class video" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(c.video_id)}?rel=0&playsinline=1"></iframe></div>
  <div class="nav"><a class="btn ${prev ? '' : 'off'}" ${link(prev)}>← Previous</a><a class="btn" target="_blank" rel="noopener" href="${esc(c.url)}">YouTube ↗</a><a class="btn ${next ? '' : 'off'}" ${link(next)}>Next →</a><button class="btn fs-btn" id="class-fullscreen" type="button" aria-label="Enter fullscreen" title="Fullscreen">⛶</button></div>` : ''}
  ${(c.resources || []).length ? '<h2>Class materials</h2>' + c.resources.map(r => `<a class="res" target="_blank" rel="noopener noreferrer" href="${esc(r.url)}">↗ ${esc(r.label || 'Open')} — ${esc(r.url.replace(/^https?:\/\//, '').slice(0, 60))}</a>`).join('') : ''}
  </div><aside class="side"><div class="eyebrow" style="margin-bottom:10px">${esc(t.name)}</div><div class="list">${t.videos.map(v => row(v, fmt(v.date), v === c, seen)).join('')}</div></aside></div>`;
  const fsButton = $app.querySelector('#class-fullscreen');
  fsButton?.addEventListener('click', async () => {
    const player = $app.querySelector('#class-player');
    if (!player) return;
    try {
      if (document.fullscreenElement === player) {
        await document.exitFullscreen();
        return;
      }
      const request = player.requestFullscreen || player.webkitRequestFullscreen;
      if (!request) {
        fsButton.textContent = 'Unavailable';
        return;
      }
      const enter = request.call(player);
      // Lock to landscape on Android browsers that support orientation locking.
      try {
        await enter;
        if (screen.orientation?.lock) await screen.orientation.lock('landscape');
      } catch (error) {
        // Fullscreen can still work when orientation locking is unsupported.
      }
    } catch (error) {
      console.warn('Fullscreen could not be started:', error);
    }
  });
  document.title = c.label + ' · Class 29';
  resolveYouTubeTitles(t.videos);
}

const notFound = () => { $app.innerHTML = '<div class="empty">Not found. <a class="btn" href="#/">Go home</a></div>'; };

function route() {
  const p = location.hash.replace(/^#\/?/, '').split('/'); document.title = 'Class 29'; window.scrollTo(0, 0);
  if (p[0] === 'g' && p[2] === 't') subject(+p[1], +p[3]);
  else if (p[0] === 'g') group(+p[1]);
  else if (p[0] === 'c') watch(decodeURIComponent(p[1] || ''));
  else home();
}

(async () => {
  try {
    const r = await fetch('./data/classes.json', { cache: 'no-store' });
    if (r.status === 401) { location.replace('/login'); return; }
    if (!r.ok) throw Error();
    lib = await r.json(); lib.groups = lib.groups || [];
    lib.groups.forEach(g => g.topics = g.topics || []); lib.groups.forEach(g => g.topics.forEach(t => t.classes = t.classes || []));
    lib.groups.sort((a,b) => rankGroup(a.name) - rankGroup(b.name) || a.name.localeCompare(b.name));
    prepare();
    syncNewClassIds();
    document.getElementById('updated').textContent = lib.updated_at ? 'Updated ' + fmt(lib.updated_at) : '';
    addEventListener('hashchange', route); route();
    // Check the published library periodically so an open tab can discover newly synced lessons.
    let lastLibraryVersion = lib.updated_at || '';
    const refreshLibrary = async () => {
      if (document.hidden) return;
      try {
        const fresh = await fetch('./data/classes.json?check=' + Date.now(), { cache: 'no-store' });
        if (!fresh.ok) return;
        const next = await fresh.json();
        if ((next.updated_at || '') === lastLibraryVersion) return;
        lib = next; lib.groups = lib.groups || [];
        lib.groups.forEach(g => { g.topics = g.topics || []; g.topics.forEach(t => t.classes = t.classes || []); });
        lib.groups.sort((a,b) => rankGroup(a.name) - rankGroup(b.name) || a.name.localeCompare(b.name));
        prepare(); syncNewClassIds();
        lastLibraryVersion = lib.updated_at || '';
        document.getElementById('updated').textContent = lib.updated_at ? 'Updated ' + fmt(lib.updated_at) : '';
        route();
      } catch (error) { console.warn('Library refresh failed', error); }
    };
    setInterval(refreshLibrary, 60000);
    addEventListener('focus', refreshLibrary);
    document.addEventListener('visibilitychange', refreshLibrary);
  } catch (e) { $app.innerHTML = '<div class="empty">Library data could not be loaded. Refresh later.</div>'; }
})();


document.addEventListener('fullscreenchange', () => {
  const player = document.querySelector('#class-player');
  const button = document.querySelector('#class-fullscreen');
  const active = !!player && document.fullscreenElement === player;
  if (button) {
    button.textContent = active ? '✕' : '⛶';
    button.setAttribute('aria-label', active ? 'Exit fullscreen' : 'Enter fullscreen');
    button.title = active ? 'Exit fullscreen' : 'Fullscreen';
  }
  if (!active) {
    try { screen.orientation?.unlock?.(); } catch (error) { /* optional browser feature */ }
  }
});
