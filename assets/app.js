const $app = document.getElementById('app');
let lib = { groups: [] }, byId = {}, freq = {};
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = v => { const d = new Date(v); return v && !isNaN(d) ? d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : ''; };
const pad = n => String(n).padStart(2, '0');
const seenSet = () => { try { return new Set(JSON.parse(localStorage.getItem('c29seen') || '[]')); } catch { return new Set(); } };
const markSeen = id => { try { const s = seenSet(); s.add(id); localStorage.setItem('c29seen', JSON.stringify([...s])); } catch { } };

// Channel banners repeat across hundreds of posts, so they are not real class names.
const isGeneric = t => (freq[t] || 0) >= 3 || /^যদি এই ক্লাস/.test(t || '');
const byTime = (a, b) => (a.date || '').localeCompare(b.date || '') || (a.telegram_message_id - b.telegram_message_id);

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
        return `<a class="card" href="#/g/${gi}"><div class="ico">${esc(g.name.trim().slice(0, 2).toUpperCase())}</div><h3>${esc(g.name)}</h3><div class="meta"><span class="pill">${g.topics.length} subjects</span><span class="pill m">${v} classes</span></div></a>`;
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
  return `<a class="item ${on ? 'on' : ''} ${seen && seen.has(c.id) ? 'seen' : ''}" href="#/c/${encodeURIComponent(c.id)}">${thumb}<span class="t"><strong>${esc(c.label)}</strong><small>${esc(no + (sub || fmt(c.date)))}</small></span></a>`;
}

function group(gi) {
  const g = lib.groups[gi]; if (!g) return notFound();
  $app.innerHTML = crumbs([['Home', '#/'], [g.name]]) + `<div class="eyebrow">Group</div><h1 style="font-size:clamp(26px,4vw,40px)">${esc(g.name)}</h1><p class="sub">${g.topics.length} subjects</p>
  <div class="grid">${g.topics.map((t, ti) => `<a class="card" href="#/g/${gi}/t/${ti}"><div class="ico">${esc(t.name.trim().slice(0, 2).toUpperCase())}</div><h3>${esc(t.name)}</h3><div class="meta"><span class="pill m">${t.videos.length} classes</span>${t.materials.length ? `<span class="pill">${t.materials.length} materials</span>` : ''}${t.last ? `<span class="pill">${fmt(t.last)}</span>` : ''}</div></a>`).join('')}</div>`;
}

function subject(gi, ti) {
  const g = lib.groups[gi], t = g?.topics[ti]; if (!t) return notFound();
  const seen = seenSet();
  $app.innerHTML = crumbs([['Home', '#/'], [g.name, '#/g/' + gi], [t.name]]) + `<div class="eyebrow">Subject</div><h1 style="font-size:clamp(26px,4vw,40px)">${esc(t.name)}</h1><p class="sub">${t.videos.length} classes</p>
  <div class="list">${t.videos.map(c => row(c, fmt(c.date), false, seen)).join('') || '<div class="empty">No video classes yet.</div>'}</div>
  ${t.materials.length ? '<h2>Materials</h2>' + t.materials.map(m => (m.resources || []).map(r => `<a class="res" target="_blank" rel="noopener noreferrer" href="${esc(r.url)}">↗ ${esc(isGeneric(m.title) ? (r.label || 'Open') : m.title)}</a>`).join('')).join('') : ''}`;
}

function watch(id) {
  const x = byId[id]; if (!x) return notFound();
  const { c, g, t, gi, ti } = x, i = t.videos.indexOf(c), prev = t.videos[i - 1], next = t.videos[i + 1], seen = seenSet();
  if (c.video_id) markSeen(c.id);
  const link = k => k ? `href="#/c/${encodeURIComponent(k.id)}"` : '';
  $app.innerHTML = crumbs([['Home', '#/'], [g.name, '#/g/' + gi], [t.name, `#/g/${gi}/t/${ti}`], [c.label]]) + `<div class="watch"><div>
  <h1 style="font-size:clamp(22px,3.5vw,32px);letter-spacing:-.5px">${esc(c.label)}</h1>
  <p class="sub">${esc(t.name)} · ${fmt(c.date)}</p>
  ${c.video_id ? `<div class="player"><iframe title="Class video" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(c.video_id)}?rel=0"></iframe></div>
  <div class="nav"><a class="btn ${prev ? '' : 'off'}" ${link(prev)}>← Previous</a><a class="btn" target="_blank" rel="noopener" href="${esc(c.url)}">YouTube ↗</a><a class="btn ${next ? '' : 'off'}" ${link(next)}>Next →</a></div>` : ''}
  ${(c.resources || []).length ? '<h2>Class materials</h2>' + c.resources.map(r => `<a class="res" target="_blank" rel="noopener noreferrer" href="${esc(r.url)}">↗ ${esc(r.label || 'Open')} — ${esc(r.url.replace(/^https?:\/\//, '').slice(0, 60))}</a>`).join('') : ''}
  </div><aside class="side"><div class="eyebrow" style="margin-bottom:10px">${esc(t.name)}</div><div class="list">${t.videos.map(v => row(v, fmt(v.date), v === c, seen)).join('')}</div></aside></div>`;
  document.title = c.label + ' · Class 29';
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
    prepare();
    document.getElementById('updated').textContent = lib.updated_at ? 'Updated ' + fmt(lib.updated_at) : '';
    addEventListener('hashchange', route); route();
  } catch (e) { $app.innerHTML = '<div class="empty">Library data could not be loaded. Refresh later.</div>'; }
})();
