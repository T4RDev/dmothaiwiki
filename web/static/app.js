// Digimon Thai Wiki - Interactive SPA Engine
// Offline-first client. Digimon dex + dmowiki-style dossier with full evolution tree.

const TABS = ['home', 'digimon', 'tamers', 'dungeons', 'patches', 'currency'];

const STATE = {
  currentTab: 'home',
  currencyRate: 0.55,
  digimon: {
    items: [],
    offset: 0,
    limit: 40,
    total: 0,
    searchQuery: '',
    rankFilter: 'all',
    attrFilter: 'all',
    elemFilter: 'all',
    sortBy: 'rank',
    hasMore: true
  },
  tamers: { items: [], series: 'all', type: 'all', skillSystem: null },
  dungeons: { items: [], map: 'all', kind: 'all' }
};

const PLACEHOLDER = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="8" fill="#131b28"/><text x="32" y="40" font-size="26" text-anchor="middle" fill="#475569">?</text></svg>'
);

const REQ_SEQ = { digi: 0, detail: 0, patch: 0 };

const SKEL = {
  pills: (widths = [64, 72, 68, 76, 62]) =>
    widths.map(w => `<span class="skel skel-pill" style="width:${w}px"></span>`).join(''),
  digimonGrid: (n = 12) => Array.from({ length: n }, () => `
    <div class="digi-card skel-card" aria-hidden="true">
      <div class="skel skel-chip"></div>
      <div class="digi-avatar-wrapper"><div class="skel skel-avatar"></div></div>
      <div class="skel skel-line lg"></div>
      <div class="skel skel-line sm"></div>
      <div class="skel-badges"><span class="skel skel-badge"></span><span class="skel skel-badge w2"></span></div>
      <div class="skel-stats"><span class="skel skel-stat"></span><span class="skel skel-stat"></span></div>
    </div>`).join(''),
  digimonDetail: () => `
    <div class="skel-detail" aria-hidden="true">
      <div class="dossier-hero skel-box">
        <div class="skel-hero-info">
          <div class="skel skel-title"></div>
          <div class="skel skel-line md"></div>
          <div class="skel-badges"><span class="skel skel-badge"></span><span class="skel skel-badge w2"></span><span class="skel skel-badge"></span></div>
          <div class="skel skel-line lg" style="margin-top:12px"></div>
          <div class="skel skel-line md"></div>
        </div>
        <div class="skel skel-hero-img"></div>
      </div>
      <div class="dossier-grid-2">
        <div class="panel"><div class="skel skel-h"></div>${Array.from({ length: 6 }, () => '<div class="skel skel-row"></div>').join('')}</div>
        <div class="panel"><div class="skel skel-h"></div>${Array.from({ length: 6 }, () => '<div class="skel skel-row"></div>').join('')}</div>
      </div>
    </div>`,
  eggs: (n = 10) => Array.from({ length: n }, () => `
    <div class="egg-card skel-egg" aria-hidden="true">
      <div class="skel skel-sq"></div>
      <div class="skel-col">
        <div class="skel skel-line lg"></div>
        <div class="skel skel-line sm"></div>
        <div class="skel-badges"><span class="skel skel-badge"></span><span class="skel skel-badge w2"></span></div>
      </div>
    </div>`).join(''),
  decks: (n = 6) => Array.from({ length: n }, () => `
    <div class="deck-card skel-deck" aria-hidden="true">
      <div class="deck-head"><div class="skel skel-line lg" style="width:55%"></div><div class="skel skel-badge"></div></div>
      <div class="skel-row-thumbs">${Array.from({ length: 4 }, () => '<span class="skel skel-thumb"></span>').join('')}</div>
      <div class="skel skel-row"></div>
      <div class="skel skel-row"></div>
    </div>`).join(''),
  dungeons: () => Array.from({ length: 3 }, () => `
    <section class="dg-map skel-dg-map" aria-hidden="true">
      <div class="dg-map-h"><div class="skel skel-line md" style="width:220px;margin:0"></div></div>
      <div class="dg-list">
        ${Array.from({ length: 3 }, () => `
          <div class="dg-card"><div class="dg-head">
            <div class="skel dg-boss" style="border-radius:10px"></div>
            <div class="dg-title"><div class="skel skel-line md" style="width:48%"></div><div class="skel skel-line sm" style="width:70%"></div></div>
            <div class="dg-badges"><span class="skel skel-badge"></span></div>
          </div></div>`).join('')}
      </div>
    </section>`).join(''),
  dungeonDetail: () => `
    <div class="skel-detail" aria-hidden="true">
      <div class="patch-nav"><span class="skel skel-pill" style="width:140px"></span></div>
      <div class="panel dg-page-head">
        <div class="skel dg-boss big"></div>
        <div style="flex:1"><div class="skel skel-title"></div><div class="skel skel-line md"></div><div class="skel skel-line sm"></div></div>
      </div>
      <div class="panel"><div class="skel skel-h"></div>${Array.from({ length: 5 }, () => '<div class="skel skel-row"></div>').join('')}</div>
    </div>`,
  patches: (n = 8) => Array.from({ length: n }, () => `
    <div class="patch-item skel-patch" aria-hidden="true">
      <div class="skel skel-pill" style="width:92px;height:22px"></div>
      <div class="patch-main"><div class="skel skel-line lg" style="width:68%"></div><div class="skel skel-line sm" style="width:45%"></div></div>
    </div>`).join(''),
  patchArticle: () => `
    <div class="skel-detail" aria-hidden="true">
      <div class="patch-nav"><span class="skel skel-pill" style="width:120px"></span><span class="skel skel-pill" style="width:150px"></span><span class="skel skel-pill" style="width:120px"></span></div>
      <article class="panel patch-article">
        <div class="patch-head"><span class="skel skel-badge"></span><div class="skel skel-title" style="margin-top:10px"></div><div class="skel skel-line sm"></div></div>
        <div class="skel skel-media"></div>
        ${Array.from({ length: 5 }, () => '<div class="skel skel-row"></div>').join('')}
      </article>
    </div>`,
  exchange: (n = 4) => `<div class="dg-exch-list" aria-hidden="true">${Array.from({ length: n }, () => '<div class="skel skel-row"></div>').join('')}</div>`,
  tamers: (n = 8) => Array.from({ length: n }, () => `
    <div class="tamer-card skel-card" aria-hidden="true">
      <div class="tm-card-top"><span class="skel skel-badge"></span><span class="skel skel-badge w2"></span></div>
      <div class="tm-body-row"><div class="skel skel-tm-img"></div><div style="flex:1"><div class="skel skel-line md"></div><div class="skel skel-line sm"></div><div class="skel skel-line sm" style="width:72%"></div></div></div>
      <div class="skel-stats"><span class="skel skel-stat"></span><span class="skel skel-stat"></span></div>
    </div>`).join(''),
  tamerDetail: () => `
    <div class="skel-detail" aria-hidden="true">
      <div class="patch-nav"><span class="skel skel-pill" style="width:140px"></span></div>
      <div class="panel tm-hero"><div class="skel tm-hero-portrait"></div><div style="flex:1;min-width:240px"><div class="skel skel-title"></div><div class="skel skel-line md"></div><div class="skel skel-row"></div><div class="skel skel-row"></div></div></div>
      <div class="panel"><div class="skel skel-h"></div>${Array.from({ length: 4 }, () => '<div class="skel skel-row"></div>').join('')}</div>
    </div>`
};

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function digiHref(slug) {
  return `/digimon/${encodeURIComponent(slug)}`;
}

function iconImg(src, alt, cls = 'ib-icon') {
  if (!src) return '';
  return `<img src="${esc(src)}" alt="${esc(alt)}" title="${esc(alt)}" class="${cls}" loading="lazy" onerror="this.style.display='none'">`;
}

function rankBadge(d, size = 'sm') {
  if (!d.rank) return `<span class="rank-chip rank-none ${size}">ไม่มี Rank</span>`;
  return `<span class="rank-chip ${size}" style="--rk:${d.rank_color}">${iconImg(d.rank_icon, 'Rank ' + d.rank, 'rank-chip-icon')}Rank ${esc(d.rank)}</span>`;
}

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  initRouter();
  initCurrencyCalculator();
  loadDigimonFilters();
  loadDigimon(true);
  loadDungeons();

  const digiSearch = document.getElementById('digi-search-input');
  if (digiSearch) {
    let debounceTimer;
    digiSearch.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        STATE.digimon.searchQuery = e.target.value.trim();
        loadDigimon(true);
      }, 250);
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      const input = document.getElementById('digi-search-input');
      if (input) input.focus();
    } else if (e.key === 'Escape') {
      navigateBack();
    }
  });
});

// ==========================================
// ROUTER (Clean History Path URLs + 404 Guard)
// ==========================================
function getRoutePath() {
  let raw = (window.location.pathname || '/').replace(/^\/+|\/+$/g, '');
  if (!raw && window.location.hash) {
    raw = window.location.hash.replace(/^#\/?/, '').trim().replace(/^\/+|\/+$/g, '');
    if (raw) {
      try {
        window.history.replaceState(null, '', '/' + raw);
      } catch (e) { }
    }
  }
  return raw;
}

function showNotFoundPage(pathStr, customMsg) {
  if (typeof disposeTamerModelViewer === 'function') disposeTamerModelViewer();
  if (typeof disposeSealLeaderViewer === 'function') disposeSealLeaderViewer();
  document.title = 'ไม่พบหน้าหรือข้อมูล - DMO Thai Wiki';
  const detailView = document.getElementById('view-digimon-detail');
  if (detailView) detailView.style.display = 'none';
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.desktop-nav .nav-link').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.mobile-bottom-nav .mobile-nav-item').forEach(item => item.classList.remove('active'));
  const nf = document.getElementById('view-not-found');
  if (nf) {
    nf.style.display = '';
    nf.classList.add('active');
    const desc = document.getElementById('not-found-desc');
    if (desc) {
      let decoded = pathStr || '';
      try { decoded = decodeURIComponent(decoded); } catch (e) { }
      desc.textContent = customMsg || (decoded
        ? `ไม่พบหน้า "/${decoded}" ในระบบ หรือลิงก์อาจถูกพิมพ์ไม่ถูกต้อง`
        : 'ลิงก์อาจถูกพิมพ์ไม่ถูกต้อง หรือไม่มีข้อมูลหน้านี้อยู่ในระบบ');
    }
  }
  window.scrollTo({ top: 0 });
}

function initRouter() {
  window.addEventListener('popstate', handleRoute);
  window.addEventListener('hashchange', handleRoute);
  document.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    if (a.target === '_blank' || a.hasAttribute('download')) return;
    const href = a.getAttribute('href') || '';
    if (!href.startsWith('/') || href.startsWith('//')) return;
    if (/^\/(api|images|models|static|favicon\.ico)\b/.test(href)) return;
    e.preventDefault();
    const extraOnClick = a.getAttribute('onclick');
    if (!extraOnClick) navigateTo(href);
  });
  handleRoute();
  document.documentElement.removeAttribute('data-boot-route');
}

function handleRoute() {
  const rawRoute = getRoutePath();
  let decodedRoute = rawRoute;
  try { decodedRoute = decodeURIComponent(rawRoute); } catch (e) { }

  if (!decodedRoute.startsWith('tamer/') && typeof disposeTamerModelViewer === 'function') {
    disposeTamerModelViewer();
  }
  if (!decodedRoute.startsWith('seal/') && typeof disposeSealLeaderViewer === 'function') {
    disposeSealLeaderViewer();
  }

  if (rawRoute === '' || rawRoute === 'home') {
    showTab('home');
  } else if (rawRoute === 'digimon') {
    showTab('digimon');
    showDexView('digimon');
  } else if (rawRoute.startsWith('digimon/')) {
    const slug = decodeURIComponent(rawRoute.slice('digimon/'.length)).trim();
    if (!slug || slug.includes('/')) { showNotFoundPage(rawRoute); return; }
    showDigimonDetailPage(slug);
  } else if (rawRoute.startsWith('patch/')) {
    const pid = decodeURIComponent(rawRoute.slice('patch/'.length)).trim();
    if (!pid || pid.includes('/')) { showNotFoundPage(rawRoute); return; }
    showTab('patches');
    openPatch(pid);
  } else if (rawRoute === 'decks' || rawRoute.startsWith('decks/')) {
    showTab('digimon');
    showDexView('decks');
    DECK_STATE.focus = rawRoute.startsWith('decks/') ? decodeURIComponent(rawRoute.slice(6)).trim() : '';
    loadDecks();
  } else if (rawRoute === 'seals' || rawRoute.startsWith('seal/')) {
    const sslug = rawRoute.startsWith('seal/') ? decodeURIComponent(rawRoute.slice(5)).trim() : '';
    if (sslug.includes('/')) { showNotFoundPage(rawRoute); return; }
    if (rawRoute === 'seal/') { showNotFoundPage(rawRoute); return; }
    showTab('digimon');
    showDexView('seals');
    if (sslug) openSeal(sslug);
    else closeSeal(true);
  } else if (rawRoute === 'dunits' || rawRoute.startsWith('dunits/')) {
    showTab('digimon');
    showDexView('dunits');
    loadDUnits();
  } else if (rawRoute === 'jogress' || rawRoute.startsWith('jogress/')) {
    const parts = rawRoute.startsWith('jogress/') ? rawRoute.slice(8).split('/').filter(Boolean) : [];
    if (parts.length > 2) { showNotFoundPage(rawRoute); return; }
    showTab('digimon');
    showDexView('jogress');
    const slug = parts.length ? decodeURIComponent(parts[0]) : '';
    if (slug && !JQ_STATE.items) {
      const lv = document.getElementById('jq-list-view');
      const dv = document.getElementById('jq-detail');
      if (lv) lv.style.display = 'none';
      if (dv) { dv.style.display = ''; dv.innerHTML = SKEL.digimonDetail(); }
    }
    loadJogressQuests().then(() => slug ? renderJogressDetail(slug, parts[1]) : showJogressList());
  } else if (rawRoute === 'tamer-status' || rawRoute === 'tamer-equip') {
    showTab('tamers');
    showTamerView('status');
  } else if (rawRoute.startsWith('tamer/')) {
    const tref = decodeURIComponent(rawRoute.slice('tamer/'.length)).trim();
    if (!tref || tref.includes('/')) { showNotFoundPage(rawRoute); return; }
    showTab('tamers');
    openTamerPage(tref);
  } else if (rawRoute.startsWith('dungeon/')) {
    const dref = decodeURIComponent(rawRoute.slice('dungeon/'.length)).trim();
    if (!dref || dref.includes('/')) { showNotFoundPage(rawRoute); return; }
    showTab('dungeons');
    openDungeonPage(dref);
  } else if (rawRoute === 'eggs' || rawRoute.startsWith('egg/')) {
    const ekey = rawRoute.startsWith('egg/') ? decodeURIComponent(rawRoute.slice(4)).trim() : '';
    if (ekey.includes('/')) { showNotFoundPage(rawRoute); return; }
    showTab('digimon');
    showDexView('eggs');
    if (ekey) openEgg(ekey);
    else closeEgg(true);
  } else if (TABS.includes(rawRoute)) {
    showTab(rawRoute);
    if (rawRoute === 'tamers') showTamerList();
    if (rawRoute === 'dungeons') showDungeonList();
    if (rawRoute === 'digimon') showDexView('digimon');
  } else {
    showNotFoundPage(rawRoute);
  }
}

function navigateTo(route, replace = false) {
  const clean = String(route || '').replace(/^#?\/?/, '').replace(/^\/+|\/+$/g, '');
  const target = clean ? '/' + clean : '/';
  if (window.location.pathname !== target || window.location.hash) {
    window.history[replace ? 'replaceState' : 'pushState'](null, '', target);
  }
  handleRoute();
}

function navigateToDigimon(slug) {
  if (slug) navigateTo(`digimon/${encodeURIComponent(slug)}`);
}

function navigateBack() {
  const rawRoute = getRoutePath();
  if (rawRoute.startsWith('digimon/')) {
    navigateTo('digimon');
  } else if (rawRoute.startsWith('tamer/')) {
    navigateTo('tamers');
  } else if (rawRoute.startsWith('dungeon/')) {
    navigateTo('dungeons');
  } else if (window.history.length > 1) {
    window.history.back();
  } else {
    navigateTo('digimon');
  }
}

function switchTab(tabId) {
  navigateTo(tabId);
}

function searchFromHome() {
  const inp = document.getElementById('home-search-input');
  const q = (inp ? inp.value : '').trim();
  navigateTo('digimon');
  const digiInp = document.getElementById('digi-search-input');
  if (digiInp) {
    digiInp.value = q;
    STATE.digimon.searchQuery = q;
    loadDigimon(true);
  }
}

function quickSearchHome(term, tab = 'digimon') {
  if (tab === 'digimon') {
    navigateTo('digimon');
    const digiInp = document.getElementById('digi-search-input');
    if (digiInp) {
      digiInp.value = term;
      STATE.digimon.searchQuery = term;
      loadDigimon(true);
    }
  } else if (tab === 'jogress') {
    navigateTo('jogress');
    const jogInp = document.getElementById('jogress-search-input');
    if (jogInp) {
      jogInp.value = term;
      filterJogressList();
    }
  } else if (tab === 'dunits') {
    navigateTo('dunits');
    const duInp = document.getElementById('dunit-search-input');
    if (duInp) {
      duInp.value = term;
      filterDUnits();
    }
  } else if (tab === 'decks') {
    navigateTo('decks');
    const dkInp = document.getElementById('deck-search-input');
    if (dkInp) {
      dkInp.value = term;
      filterDecks();
    }
  } else if (tab === 'dungeons') {
    navigateTo('dungeons');
    const dgInp = document.getElementById('dungeon-search-input');
    if (dgInp) {
      dgInp.value = term;
      filterDungeons();
    }
  } else {
    navigateTo(tab);
  }
}

function showTab(tabId) {
  STATE.currentTab = tabId;
  document.title = 'DMO Thai Wiki - เซิร์ฟเวอร์ไทย';

  const detailView = document.getElementById('view-digimon-detail');
  if (detailView) detailView.style.display = 'none';
  const nf = document.getElementById('view-not-found');
  if (nf) nf.style.display = 'none';

  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  const targetPanel = document.getElementById(`tab-${tabId}`);
  if (targetPanel) targetPanel.classList.add('active');

  document.querySelectorAll('.desktop-nav .nav-link').forEach(btn => {
    const oc = btn.getAttribute('onclick') || '';
    btn.classList.toggle('active', oc.includes(`'${tabId}'`));
  });
  document.querySelectorAll('.mobile-bottom-nav .mobile-nav-item').forEach(item => {
    const oc = item.getAttribute('onclick') || '';
    item.classList.toggle('active', oc.includes(`'${tabId}'`));
  });

  if (tabId === 'tamers') { loadTamers(); }
  if (tabId === 'patches') { loadPatches(); if (!getRoutePath().startsWith('patch/')) closePatch(true); }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================
// 1. DIGIMON DEX
// ==========================================
async function loadDigimonFilters() {
  try {
    const res = await fetch('/api/digimon-filters');
    const f = await res.json();

    const rankEl = document.getElementById('rank-pills');
    if (rankEl) {
      rankEl.innerHTML =
        `<button class="filter-pill active" data-val="all">ทั้งหมด</button>` +
        f.ranks.map(r => `<button class="filter-pill icon-pill" data-val="${esc(r.name)}">${iconImg(r.icon, r.name, 'pill-icon')}${esc(r.name)} <small>${r.count}</small></button>`).join('') +
        `<button class="filter-pill" data-val="none">ไม่มี Rank <small>${f.no_rank}</small></button>`;
      bindPills(rankEl, v => { STATE.digimon.rankFilter = v; loadDigimon(true); });
    }

    const pillRow = (id, list, key) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.innerHTML =
        `<button class="filter-pill active" data-val="all">ทั้งหมด</button>` +
        list.map(a => `<button class="filter-pill icon-pill" data-val="${esc(a.name)}" title="${esc(a.name)}">${iconImg(a.icon, a.name, 'pill-icon')}${esc(a.th || a.name)} <small>${a.count}</small></button>`).join('');
      bindPills(el, v => { STATE.digimon[key] = v; loadDigimon(true); });
    };
    pillRow('attr-pills', f.attributes, 'attrFilter');
    pillRow('elem-pills', f.elements, 'elemFilter');
  } catch (err) {
    console.error('Failed to load filters:', err);
  }
}

function bindPills(container, onPick) {
  container.addEventListener('click', (e) => {
    const btn = e.target.closest('.filter-pill');
    if (!btn) return;
    container.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    onPick(btn.dataset.val);
  });
}

async function loadDigimon(reset = false) {
  const seq = ++REQ_SEQ.digi;
  const grid = document.getElementById('digimon-grid');
  const loadBtn = document.getElementById('load-more-btn');
  if (reset) {
    STATE.digimon.offset = 0;
    STATE.digimon.items = [];
    STATE.digimon.hasMore = true;
    if (grid) grid.innerHTML = SKEL.digimonGrid(12);
    if (loadBtn) loadBtn.style.display = 'none';
  } else if (loadBtn) {
    loadBtn.disabled = true;
    loadBtn.textContent = 'กำลังโหลด...';
  }

  const { searchQuery, rankFilter, attrFilter, elemFilter, offset, limit, sortBy } = STATE.digimon;
  const params = new URLSearchParams({ offset, limit, sort: sortBy });
  if (searchQuery) params.append('q', searchQuery);
  if (rankFilter !== 'all') params.append('rank', rankFilter);
  if (attrFilter !== 'all') params.append('attribute', attrFilter);
  if (elemFilter !== 'all') params.append('element', elemFilter);

  try {
    const res = await fetch(`/api/digimon?${params.toString()}`);
    const data = await res.json();
    if (seq !== REQ_SEQ.digi) return;
    STATE.digimon.total = data.total;
    STATE.digimon.items = reset ? data.items : STATE.digimon.items.concat(data.items);
    STATE.digimon.offset += data.items.length;
    STATE.digimon.hasMore = STATE.digimon.items.length < data.total;

    renderDigimonGrid(STATE.digimon.items);

    const countDisplay = document.getElementById('digi-count-display');
    if (countDisplay) countDisplay.textContent = data.total.toLocaleString();
    if (loadBtn) {
      loadBtn.disabled = false;
      loadBtn.textContent = 'โหลดดิจิมอนเพิ่มเติม';
      loadBtn.style.display = STATE.digimon.hasMore ? 'inline-block' : 'none';
    }
  } catch (err) {
    if (seq !== REQ_SEQ.digi) return;
    console.error('Failed to load digimon:', err);
    if (reset && grid) grid.innerHTML = '<div class="empty-note">โหลดข้อมูลไม่สำเร็จ ลองรีเฟรชอีกครั้ง</div>';
    if (loadBtn) {
      loadBtn.disabled = false;
      loadBtn.textContent = 'โหลดดิจิมอนเพิ่มเติม';
    }
  }
}

function renderDigimonGrid(items) {
  const grid = document.getElementById('digimon-grid');
  if (!grid) return;
  if (items.length === 0) {
    grid.innerHTML = '<div class="empty-note">ไม่พบข้อมูลดิจิมอนที่ตรงกับเงื่อนไข</div>';
    return;
  }

  grid.innerHTML = items.map(d => {
    const hp = d.stats?.HP?.max !== '-' ? d.stats?.HP?.max : (d.stats?.HP?.base || '-');
    const at = d.stats?.AT?.max !== '-' ? d.stats?.AT?.max : (d.stats?.AT?.base || '-');
    return `
      <a class="digi-card" href="${digiHref(d.slug)}">
        <div class="card-rank">${rankBadge(d)}</div>
        <div class="digi-avatar-wrapper">
          <img src="${esc(d.image || d.icon || PLACEHOLDER)}" alt="${esc(d.title)}" class="digi-avatar" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
        </div>
        <div class="digi-name-en">${esc(d.thai_name || d.title)}</div>
        <div class="digi-name-th">${d.thai_name ? esc(d.title) : ''}</div>
        <div class="digi-badges">
          ${d.attribute ? `<span class="badge icon-badge">${iconImg(d.attribute_icon, d.attribute, 'badge-icon')}${esc(d.attribute_th || d.attribute)}</span>` : ''}
          ${d.element ? `<span class="badge icon-badge">${iconImg(d.element_icon, d.element, 'badge-icon')}${esc(d.element_th || d.element)}</span>` : ''}
          ${d.form ? `<span class="badge">${esc(d.form_th || d.form)}</span>` : ''}
          ${(d.aoe_slots || []).length ? `<span class="aoe-badge" style="margin-left:0">สกิลหมู่ ${d.aoe_slots.map(n => 'F' + n).join(',')}</span>` : ''}
        </div>
        <div class="digi-quick-stats">
          <span>AT: <strong style="color:#fbbf24;">${esc(at)}</strong></span>
          <span>HP: <strong style="color:#ef4444;">${esc(hp)}</strong></span>
        </div>
      </a>`;
  }).join('');
}

function onFilterChange() {
  STATE.digimon.sortBy = document.getElementById('sort-select').value;
  loadDigimon(true);
}

function loadMoreDigimon() {
  if (STATE.digimon.hasMore) loadDigimon(false);
}

// ==========================================
// EVOLUTION TREE (dmowiki "Digivolves" layout)
// ==========================================
function renderEvoBranch(n) {
  const node = n.in_thai === false ? `
    <span class="evo-tnode not-thai" title="${esc(n.title)} — ยังไม่มีในเซิร์ฟไทย">
      <img src="${esc(n.icon || PLACEHOLDER)}" alt="${esc(n.title)}" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
      <span class="evo-tnode-flag">ไม่มีในไทย</span>
      <span class="evo-tnode-name">${esc(n.thai || n.title)}</span>
    </span>` : `
    <a class="evo-tnode ${n.current ? 'is-current' : ''}" href="${digiHref(n.slug)}" title="${esc(n.title)}${n.rank ? ' — Rank ' + esc(n.rank) : ''}${n.form ? ' — ' + esc(n.form) : ''}">
      <img src="${esc(n.icon || PLACEHOLDER)}" alt="${esc(n.title)}" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
      ${n.rank ? `<span class="evo-tnode-rank">${esc(n.rank)}</span>` : ''}
      <span class="evo-tnode-name">${esc(n.thai || n.title)}</span>
    </a>`;
  // dmowiki layout: first child continues to the right (→), the others drop below the
  // parent and branch off with ↳, each one rendered recursively the same way.
  const kids = n.children || [];
  const arrow = c => `<span class="evo-h">${c.jogress ? '<em>Jogress</em>' : ''}</span>`;
  const [first, ...rest] = kids;
  return `
    <div class="evo-b">
      <div class="evo-row">
        <div class="evo-col">${node}${rest.length ? '<div class="evo-stem"></div>' : ''}</div>
        ${first ? arrow(first) + renderEvoBranch(first) : ''}
      </div>
      ${rest.map((c, i) => `
        <div class="evo-down ${i === rest.length - 1 ? 'last' : ''}">
          ${arrow(c)}${renderEvoBranch(c)}
        </div>`).join('')}
    </div>`;
}

function renderEvoTree(tree) {
  if (!tree || tree.length === 0) {
    return '<div class="empty-note small">ไม่มีข้อมูลสายวิวัฒนาการใน dmowiki</div>';
  }
  return `<div class="evo-tree">${tree.map(r => `<div class="evo-root">${renderEvoBranch(r)}</div>`).join('')}</div>`;
}

// ==========================================
// DOSSIER PAGE
// ==========================================
// Thai first, original English small behind it
function thEn(th, en) {
  if (th && en && th !== en) return `${esc(th)} <small class="en">${esc(en)}</small>`;
  return esc(th || en || '');
}

function itemList(items) {
  return items.map(i => `<div class="ib-item">${iconImg(i.icon, i.name)}<span>${thEn(i.th, i.name)}</span></div>`).join('');
}

// "4.5 seconds cooldown" -> "คูลดาวน์ 4.5 วินาที" etc. (numbers are kept exactly as on the wiki)
function skillMetaTh(s) {
  if (!s || s === '-') return s || '-';
  let clean = String(s).replace(/,/g, '.').trim();
  return clean
    .replace(/^([\d.?]+)\s*seconds?\s*cooldown$/i, 'คูลดาวน์ $1 วินาที')
    .replace(/^([\d.?]+)\s*DS consumed$/i, 'ใช้ DS $1')
    .replace(/^([\d?]+)\s*skill points?\s*per upgrade$/i, 'ใช้ $1 แต้มสกิลต่อการอัป')
    .replace(/^([\d.?]+)\s*seconds?\s*animation$/i, 'เวลาร่าย $1 วินาที');
}

const ELEM_TH = { Fire: 'ไฟ', Water: 'น้ำ', Ice: 'น้ำแข็ง', Wind: 'ลม', Thunder: 'สายฟ้า', Land: 'ดิน', Wood: 'ไม้', Steel: 'เหล็ก', Light: 'แสง', 'Pitch Black': 'มืดมิด', Neutral: 'ไร้ธาตุ' };
function skillElemTh(s) {
  const m = /^(.+?) attribute$/i.exec(s || '');
  return m && ELEM_TH[m[1]] ? `ธาตุ${ELEM_TH[m[1]]}` : (s || '');
}

function ibRow(label, value) {
  if (!value) return '';
  return `<tr><th>${label}</th><td>${value}</td></tr>`;
}

async function showDigimonDetailPage(slug) {
  const seq = ++REQ_SEQ.detail;
  const nf = document.getElementById('view-not-found');
  if (nf) nf.style.display = 'none';
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.desktop-nav .nav-link').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.mobile-bottom-nav .mobile-nav-item').forEach(item => item.classList.remove('active'));

  const detailView = document.getElementById('view-digimon-detail');
  const breadcrumbs = document.getElementById('detail-breadcrumbs');
  const content = document.getElementById('detail-page-content');
  if (!detailView || !content) return;

  detailView.style.display = 'block';
  window.scrollTo({ top: 0 });
  if (breadcrumbs) breadcrumbs.innerHTML = SKEL.pills([96, 68, 110]);
  content.innerHTML = SKEL.digimonDetail();

  try {
    const res = await fetch(`/api/digimon/${encodeURIComponent(slug)}`);
    if (!res.ok) throw new Error('Digimon not found');
    const { digimon: d } = await res.json();
    if (seq !== REQ_SEQ.detail) return;
    const stats = d.stats || {};
    const skills = d.skills || [];
    const passives = d.passives || [];

    document.title = `${d.thai_name || d.title} - DMO Thai Wiki - เซิร์ฟเวอร์ไทย`;

    if (breadcrumbs) {
      breadcrumbs.innerHTML = `
        <a href="/digimon">สารานุกรมดิจิมอน</a>
        <span class="sep">›</span>
        ${rankBadge(d)}
        <span class="sep">›</span>
        <span class="active-crumb">${esc(d.thai_name || d.title)}</span>`;
    }

    const evoFrom = (d.evo_from_names || []).map((n, i) => thEn((d.evo_from_th || [])[i], n)).join(d.evo_kind === 'Jogress' ? ' <b>+</b> ' : '<br>');
    const yesTh = v => v.replace(/^Yes/, 'ได้');
    const ride = d.can_ride && d.can_ride.startsWith('Yes') ? `ได้ (${esc(yesTh(d.can_ride))})` : 'ไม่ได้';
    const hatch = d.can_hatch && d.can_hatch.startsWith('Yes') ? `ได้ (${esc(yesTh(d.can_hatch))}) <a class="egg-link" href="/egg/${encodeURIComponent(d.slug)}"><img src="/images/ui/ui_egg.png" class="btn-game-icon" alt=""> ดูไข่</a>` : 'ไม่ได้';
    const lore = d.lore_th || d.lore;

    const statRows = [
      ['HP', 'Health Points', '#ef4444'], ['DS', 'Digi-Soul', '#38bdf8'], ['AT', 'Attack', '#f59e0b'],
      ['AS', 'Attack Speed', '#10b981'], ['CT', 'Critical Hit', '#fbbf24'], ['HT', 'Hit Rate', '#a855f7'],
      ['DE', 'Defense', '#3b82f6'], ['EV', 'Evade', '#34d399']
    ].map(([k, label, color]) => `
      <tr>
        <td><img src="/images/${k}.png" class="stat-icon" alt="" onerror="this.style.display='none'"><strong>${k}</strong></td>
        <td style="color:${color}; font-weight:700; text-align:right;">${esc(stats[k]?.max || '-')}</td>
        <td style="text-align:right;">${esc(stats[k]?.base || '-')}</td>
      </tr>`).join('');

    content.innerHTML = `
      <div class="dossier-hero">
        <div>
          <div class="hero-title-row">
            <h1>${esc(d.thai_name || d.title)}</h1>
            ${rankBadge(d, 'lg')}
          </div>
          <div class="hero-sub">
            ${d.thai_name ? esc(d.title) : ''}
            ${d.jp_name ? `<span class="hero-jp">(${esc(d.jp_name)})</span>` : ''}
          </div>
          ${d.kr_name || d.cn_name ? `<div class="hero-langs">${d.kr_name ? `เกาหลี: ${esc(d.kr_name)}` : ''}${d.kr_name && d.cn_name ? ' · ' : ''}${d.cn_name ? `จีน: ${esc(d.cn_name)}` : ''}</div>` : ''}
        </div>
        <div class="hero-badges">
          ${d.in_thai === false ? '<span class="badge lg not-thai-badge">ยังไม่มีในเซิร์ฟไทย</span>' : ''}
          ${d.attribute ? `<span class="badge icon-badge lg">${iconImg(d.attribute_icon, d.attribute, 'badge-icon')}${esc(d.attribute_th || d.attribute)}</span>` : ''}
          ${d.element ? `<span class="badge icon-badge lg">${iconImg(d.element_icon, d.element, 'badge-icon')}${esc(d.element_th || d.element)}</span>` : ''}
          ${d.form ? `<span class="badge lg">${esc(d.form_th || d.form)}</span>` : ''}
        </div>
      </div>

      <div class="wiki-layout">
        <div class="wiki-main">
          ${lore ? `<div class="panel"><h3 class="panel-title">ประวัติ</h3><p class="lore">${esc(lore)}</p></div>` : ''}

          <div class="panel">
            <h3 class="panel-title">สายวิวัฒนาการ <span>กดที่ตัวไหนเพื่อเปิดข้อมูลตัวนั้น</span></h3>
            <div class="evo-scroll">${renderEvoTree(d.tree)}</div>
          </div>

          <div class="panel">
            <h3 class="panel-title">ค่าสเตตัส <span>สเตตัสสูงสุด (ขนาด 140% ระดับ 180) เทียบกับค่าพื้นฐาน (ขนาด 100% ระดับ 1)</span></h3>
            <div class="table-responsive">
              <table class="stats-compare-table">
                <thead><tr><th>ค่าพลัง</th><th style="text-align:right;">สเตตัสสูงสุด</th><th style="text-align:right;">ค่าพื้นฐาน</th></tr></thead>
                <tbody>${statRows}</tbody>
              </table>
            </div>
          </div>

          ${renderEffects(d, await getRankTable())}

          ${skills.length ? `
            <div class="panel">
              <div class="skills-head">
                <h3 class="panel-title">สกิลโจมตี${(d.aoe_slots || []).length ? ` <span>สกิลหมู่ (ตีวงกว้าง): ${d.aoe_slots.map(n => 'F' + n).join(', ')}</span>` : ''}</h3>
                <div class="skill-slider">
                  <label>ระดับสกิล: <strong id="skill-lv-badge">Lv. 1</strong></label>
                  <input type="range" id="skill-slider" min="1" max="25" value="1" oninput="updateSkillDamage(this.value)">
                </div>
              </div>
              ${skills.map((s, idx) => `
                <div class="skill-card-detail">
                  <div class="skill-header-row">
                    <div><strong>F${idx + 1}: ${thEn(s.name_th, s.name)}</strong>${s.element ? ` <span class="badge">${esc(skillElemTh(s.element))}</span>` : ''}${aoeBadge(s.aoe)}</div>
                    <div class="skill-dmg">ดาเมจ: <span class="skill-dmg-val" data-levels="${esc(JSON.stringify(s.levels))}">${esc(s.levels[0] || '-')}</span></div>
                  </div>
                  <div class="skill-meta-tags">
                    <span class="skill-meta-tag"><img src="/images/AS.png" class="stat-icon-inline" alt="CD"> ${esc(skillMetaTh(s.cooldown))}</span>
                    <span class="skill-meta-tag"><img src="/images/DS.png" class="stat-icon-inline" alt="DS"> ${esc(skillMetaTh(s.ds_consumed))}</span>
                    <span class="skill-meta-tag">แต้ม: ${esc(skillMetaTh(s.upgrade_points))}</span>
                    <span class="skill-meta-tag">อนิเมชัน: ${esc(skillMetaTh(s.animation))}</span>
                  </div>
                  ${(s.description_th || s.description) ? `<div class="skill-desc">${esc(s.description_th || s.description)}</div>` : ''}
                </div>`).join('')}
              <button class="preset-btn full-btn" onclick="toggleFullSkillTable()">เปิด/ปิด ตารางดาเมจเต็ม 25 เลเวล</button>
              <div id="full-skill-table-wrapper" style="display:none; margin-top:14px;" class="table-responsive">
                <table class="custom-table" style="font-size:0.75rem;">
                  <thead><tr><th>สกิล</th>${Array.from({ length: 25 }, (_, i) => `<th>Lv.${i + 1}</th>`).join('')}</tr></thead>
                  <tbody>${skills.map(s => `<tr><td><strong>${esc(s.name_th || s.name)}</strong></td>${s.levels.map(lv => `<td>${esc(lv)}</td>`).join('')}</tr>`).join('')}</tbody>
                </table>
              </div>
            </div>` : ''}
        </div>

        <aside class="wiki-infobox">
          <div class="ib-title">${esc(d.thai_name || d.title)}</div>
          <div class="ib-portrait">
            <img src="${esc(d.image || d.icon || PLACEHOLDER)}" alt="${esc(d.title)}" onerror="this.src='${PLACEHOLDER}'">
          </div>
          <table class="ib-table">
            <tbody>
              ${ibRow('Rank', d.rank ? `<div class="ib-item">${iconImg(d.rank_icon, d.rank)}<span style="color:${d.rank_color}; font-weight:800;">${esc(d.rank)}</span></div>` : '<span class="muted">— (ต่ำกว่าร่างสุดยอด)</span>')}
              ${ibRow('ปลดล็อกที่ระดับ', esc(d.unlock_level))}
              ${ibRow('ไอเทมปลดร่าง', itemList(d.unlock_items || []))}
              ${ibRow('ไอเทมโหมดขี่', itemList(d.ride_items || []) + (d.ride_source && d.ride_source !== 'dmowiki' ? `<small class="muted">ที่มา: ${esc(d.ride_source)}</small>` : ''))}
              ${ibRow('ร่าง', thEn(d.form_th, d.form))}
              ${ibRow('แอตทริบิวต์', d.attribute ? `<div class="ib-item">${iconImg(d.attribute_icon, d.attribute)}<span>${thEn(d.attribute_th, d.attribute)}</span></div>` : '')}
              ${ibRow('ธาตุ', d.element ? `<div class="ib-item">${iconImg(d.element_icon, d.element)}<span>${thEn(d.element_th, d.element)}</span></div>` : '')}
              ${ibRow('ประเภทการโจมตี', d.attacker_type ? `<div class="ib-item">${iconImg(d.attacker_icon, d.attacker_type, 'ib-icon wide')}<span>${thEn(d.attacker_type_th, d.attacker_type)}</span></div>` : '')}
              ${ibRow('ชนิด', thEn(d.type_th, d.type))}
              ${ibRow('ตระกูล', (d.families || []).map(f => `<div class="ib-item">${iconImg(f.icon, f.name)}<span>${thEn(f.th, f.name)}</span></div>`).join(''))}
              ${ibRow(d.evo_kind === 'Jogress' ? 'โจเกรสจาก' : 'วิวัฒนาการมาจาก', evoFrom)}
              ${ibRow('เงื่อนไขวิวัฒนาการ', esc(d.required_to_evolve))}
              ${ibRow('สถานที่พบ', thEn(d.location_th, d.location))}
              ${ibRow('ขี่ได้', ride)}
              ${ibRow('ฟักไข่ได้', hatch)}
              ${(d.decks || []).length ? ibRow('เด็ค', d.decks.map(x => `<a class="egg-link" style="margin-left:0; display:block" href="/decks/${encodeURIComponent(x.name)}"><img src="/images/ui/ui_deck.png" class="btn-game-icon" alt=""> ${esc(x.name)}</a>`).join('')) : ''}
              ${d.has_jogress_quest ? ibRow('เควสโจเกรส', `<a class="egg-link" style="margin-left:0" href="/jogress/${encodeURIComponent(d.slug)}"><img src="/images/ui/ui_jogress.png" class="btn-game-icon" alt=""> ดูเควสโจเกรส</a>`) : ''}
              ${ibRow('มีในเกม', d.available === 'Yes' ? '<span class="avail-yes">มี</span>' : esc(d.available || '-'))}
              ${d.thai_name_unofficial ? ibRow('หมายเหตุ', '<small class="muted">ชื่อไทยถอดเสียงโดยเว็บ (ไม่ใช่ชื่อทางการ)</small>') : ''}
            </tbody>
          </table>
        </aside>
      </div>`;

    const cur = content.querySelector('.evo-tnode.is-current');
    if (cur) cur.scrollIntoView({ block: 'nearest', inline: 'center' });
  } catch (err) {
    console.error('Failed to load digimon dossier:', err);
    content.innerHTML = `
      <div class="empty-note">
        <div style="font-size:1.1rem; font-weight:700; color:var(--color-danger);">ไม่พบข้อมูลดิจิมอน '${esc(slug)}'</div>
        <button class="preset-btn" style="margin-top:14px; padding:8px 20px;" onclick="navigateBack()">ย้อนกลับไปสารานุกรม</button>
      </div>`;
  }
}

// ==========================================
// RANK PASSIVES / SKILL SPECIAL EFFECTS / PROS & CONS (dmowiki-style, Thai)
// ==========================================
const FIELD_TH = {
  'Activation': 'โอกาสทำงาน', 'Duration': 'ระยะเวลา', 'Buff Effect': 'ผลบัฟ', 'Debuff Effect': 'ผลดีบัฟ',
  'Effect': 'ผล', 'Stack Effect': 'ผลแบบสะสม', 'Note': 'หมายเหตุ', 'Cooldown': 'คูลดาวน์', 'Max Stack': 'สะสมสูงสุด'
};
const GROUP_TH = { Vaccine: 'วัคซีน', Virus: 'ไวรัส', Data: 'ดาต้า', Unknown: 'อันโนว์น', ...ELEM_TH };
const RANK_ROWS = ['SSS', 'SSS+', 'U'];
let RANK_TABLE = null;
async function getRankTable() {
  if (RANK_TABLE) return RANK_TABLE;
  try { RANK_TABLE = await (await fetch('/api/rank-table')).json(); } catch (e) { RANK_TABLE = {}; }
  return RANK_TABLE;
}

function fieldRows(fields) {
  return fields.map(([lab, en, th]) => `
    <div class="fx-row"><span class="fx-lab">${esc(FIELD_TH[lab] || lab)}</span><span class="fx-val">${esc(th || en)}</span></div>`).join('');
}

function groupIcon(d, g) {
  if (g === d.attribute) return d.attribute_icon;
  if (g === d.element) return d.element_icon;
  return '';
}

const AOE_SHAPE_TH = { self: 'รอบตัวเรา', target: 'รอบเป้าหมาย', line: 'แนวเส้นตรง' };
const AOE_SIZE_TH = { Small: 'แคบ', Medium: 'กลาง', Wide: 'กว้าง', Maximum: 'กว้างสุด' };
function aoeBadge(a) {
  if (!a) return '';
  const bits = [AOE_SHAPE_TH[a.shape], AOE_SIZE_TH[a.size] && `ระยะ${AOE_SIZE_TH[a.size]}`].filter(Boolean).join(' · ');
  return ` <span class="aoe-badge" title="สกิลโจมตีหมู่ ตีศัตรูหลายตัวพร้อมกัน">สกิลหมู่${bits ? ` · ${bits}` : ''}</span>`;
}

function renderEffects(d, rankTable) {
  const rp = d.rank_passives || [];
  const fx = d.skill_effects || [];
  const ov = d.overview || { pros: [], cons: [] };
  const skillName = slot => {
    const i = parseInt(slot.slice(1)) - 1;
    const s = (d.skills || [])[i];
    return s ? (s.name_th || s.name) : '';
  };
  let html = '';

  if (rp.length) {
    html += `
      <div class="panel fx-panel">
        <h3 class="panel-title">ความสามารถติดตัวตาม Rank <span>Rank ${esc(d.rank)} · ผลตามแอตทริบิวต์และธาตุของดิจิมอนตัวนี้</span></h3>
        <div class="fx-grid">
          ${rp.map(g => `
            <div class="fx-card">
              <div class="fx-head">${iconImg(groupIcon(d, g.group), g.group, 'badge-icon')}<strong>${esc(GROUP_TH[g.group] || g.group)}</strong> <small class="en">${esc(g.group)}</small>
                ${g.derived ? '<span class="fx-tag" title="หน้า wiki ไม่ได้เขียนไว้ ใช้ค่าจาก Rank และธาตุเดียวกัน">ตามตาราง Rank</span>' : ''}</div>
              ${fieldRows(g.fields)}
            </div>`).join('')}
        </div>
        ${renderRankCompare(d, rankTable)}
      </div>`;
  }

  if (fx.length) {
    html += `
      <div class="panel fx-panel">
        <h3 class="panel-title">เอฟเฟกต์พิเศษของสกิล <span>บัฟ/ดีบัฟที่เกิดเมื่อใช้สกิล</span></h3>
        <div class="fx-grid">
          ${fx.map(e => `
            <div class="fx-card">
              <div class="fx-head"><span class="fx-slot">${esc(e.slot)}</span><strong>${esc(skillName(e.slot) || e.skill)}</strong>${aoeBadge(((d.skills || [])[parseInt(e.slot.slice(1)) - 1] || {}).aoe)}
                ${e.skill && skillName(e.slot) && skillName(e.slot) !== e.skill ? `<small class="en">${esc(e.skill)}</small>` : ''}</div>
              ${e.name ? `<div class="fx-buffname">${esc(e.name)}</div>` : ''}
              ${fieldRows(e.fields)}
            </div>`).join('')}
        </div>
      </div>`;
  }

  if (ov.pros.length || ov.cons.length) {
    const list = items => items.map(([en, th]) => `<li>${esc(th || en)}</li>`).join('');
    html += `
      <div class="panel fx-panel">
        <h3 class="panel-title">ภาพรวม <span>ข้อดีและข้อเสีย</span></h3>
        <div class="fx-procon">
          ${ov.pros.length ? `<div class="fx-pros"><h4>ข้อดี</h4><ul>${list(ov.pros)}</ul></div>` : ''}
          ${ov.cons.length ? `<div class="fx-cons"><h4>ข้อเสีย</h4><ul>${list(ov.cons)}</ul></div>` : ''}
        </div>
      </div>`;
  }
  return html;
}

// Same attribute / element across Rank SSS, SSS+ and U, so players can see what ranking up changes
function renderRankCompare(d, table) {
  const groups = [d.attribute, d.element].filter(g => g && RANK_ROWS.some(r => table[r] && table[r][g]));
  if (!groups.length) return '';
  const cell = (r, g) => {
    const f = (table[r] || {})[g];
    if (!f) return '<td class="muted">-</td>';
    const main = f.find(x => x[0] === 'Stack Effect' || x[0] === 'Effect') || f[0];
    return `<td>${esc(main[2] || main[1])}</td>`;
  };
  return `
    <details class="fx-compare">
      <summary>เทียบผลติดตัวของ Rank SSS / SSS+ / U (แอตทริบิวต์และธาตุเดียวกัน)</summary>
      <div class="table-responsive">
        <table class="custom-table">
          <thead><tr><th>Rank</th>${groups.map(g => `<th>${esc(GROUP_TH[g] || g)}</th>`).join('')}</tr></thead>
          <tbody>${RANK_ROWS.map(r => `<tr class="${r === d.rank ? 'cur' : ''}"><td><strong>${r}</strong></td>${groups.map(g => cell(r, g)).join('')}</tr>`).join('')}</tbody>
        </table>
      </div>
    </details>`;
}

function updateSkillDamage(level) {
  const badge = document.getElementById('skill-lv-badge');
  if (badge) badge.textContent = `Lv. ${level}`;
  document.querySelectorAll('.skill-dmg-val').forEach(el => {
    try {
      const levels = JSON.parse(el.getAttribute('data-levels'));
      el.textContent = levels[parseInt(level) - 1] || levels[0] || '-';
    } catch (e) { }
  });
}

function toggleFullSkillTable() {
  const wrapper = document.getElementById('full-skill-table-wrapper');
  if (wrapper) wrapper.style.display = wrapper.style.display === 'none' ? 'block' : 'none';
}

// ==========================================
// 3. DUNGEONS (Thai client: dungeon tables, monsters, NPCs, quests, exchange)
// ==========================================

const fmtNum = n => Number(n || 0).toLocaleString();

function fmtMoney(n) {
  n = Math.floor(Number(n || 0));
  const t = Math.floor(n / 1e6), m = Math.floor((n % 1e6) / 1e3), b = n % 1e3;
  const parts = [];
  if (t) parts.push(`<b class="money-t">${t.toLocaleString()}</b> T`);
  if (m) parts.push(`<b class="money-m">${m}</b> M`);
  if (b || !parts.length) parts.push(`<b class="money-b">${b}</b> B`);
  return `<span class="dg-money"><img src="/images/ui/ui_money.png" class="btn-game-icon" alt="เงิน"> ${parts.join(' ')}</span>`;
}

function dgItem(it, small) {
  if (!it) return '';
  return `<span class="jq-item${small ? ' sm' : ''}" title="${esc(it.name)}">${it.icon ? `<img src="${esc(it.icon)}" alt="" onerror="this.remove()">` : ''}${esc(it.name)}${it.count > 1 ? ` ×${fmtNum(it.count)}` : ''}</span>`;
}

function dgNpcPic(n, big) {
  return n && n.icon ? `<img class="dg-npc-pic${big ? ' big' : ''}" src="${esc(n.icon)}" alt="" onerror="this.remove()">`
    : `<span class="dg-npc-pic${big ? ' big' : ''} none"></span>`;
}

function dgNpc(n) {
  return `<span class="dg-npc">${dgNpcPic(n)}<span class="dg-npc-txt"><b>${esc(n.name)}</b>${n.title ? ` <small class="muted">&lt;${esc(n.title)}&gt;</small>` : ''}
    <span class="dg-where">${n.map ? esc(n.map) : 'NPC กิจกรรม / ไม่ได้ยืนประจำแมพ'}</span></span></span>`;
}

function dgMonName(m) {
  const inner = `${m.icon ? `<img src="${esc(m.icon)}" alt="" onerror="this.remove()">` : ''}<span>${esc(m.name)}${m.title ? ` <small class="muted">&lt;${esc(m.title)}&gt;</small>` : ''}</span>`;
  return m.slug ? `<a class="dg-mon" href="${digiHref(m.slug)}">${inner}</a>` : `<span class="dg-mon">${inner}</span>`;
}

function dgDetail(d) {
  const kills = d.steps.filter(s => s.kind === 1 && s.monster);
  return `
    <div class="dg-detail">
      ${d.desc ? `<div class="dg-desc">${esc(d.desc).replace(/\n/g, '<br>')}</div>` : ''}
      <div class="dg-grid">
        <div class="panel">
          <h4>การเข้าดันเจี้ยน</h4>
          ${d.instance ? `
            <div class="dg-row"><span class="egg-lab">NPC พาเข้า</span><div>${d.entry_npcs.length ? d.entry_npcs.map(dgNpc).join('') : '<span class="muted">ไม่พบ NPC ในไฟล์ (เข้าผ่านเควสหรือกิจกรรม)</span>'}</div></div>
            <div class="dg-row"><span class="egg-lab">บัตรผ่าน</span><div>${d.ticket ? dgItem(d.ticket) : '<span class="muted">ไม่ต้องใช้บัตร</span>'}</div></div>
            <div class="dg-row"><span class="egg-lab">จำนวนคน</span><div>${d.players ? `สูงสุด ${d.players} คน` : '-'}</div></div>`
      : `<div class="dg-row"><span class="egg-lab">แมพ</span><div>เดินเข้าได้เลยที่แมพ <b>${esc(d.map)}</b> ไม่ต้องคุย NPC</div></div>`}
          <div class="dg-row"><span class="egg-lab">เลเวลมอน</span><div>${d.level_range.length ? `Lv.${d.level_range[0]}${d.level_range[1] !== d.level_range[0] ? ' - ' + d.level_range[1] : ''}` : '-'}${d.level_hint ? ` · เกมแนะนำดิจิมอน Lv.${d.level_hint}` : ''}</div></div>
        </div>
        ${kills.length ? `<div class="panel"><h4>ภารกิจในดันเจี้ยน (ตามลำดับ)</h4><ol class="dg-steps">${kills.map(s => `<li>กำจัด ${dgMonName(s.monster)} <b>×${s.count}</b></li>`).join('')}</ol></div>` : ''}
      </div>
      <div class="panel">
        <h4>มอนสเตอร์ในดันเจี้ยน <span>${d.monsters.length} ตัว</span></h4>
        ${d.monsters.length ? `<div class="table-responsive"><table class="custom-table dg-mon-table"><thead><tr><th>มอนสเตอร์</th><th>เลเวล</th><th>HP</th></tr></thead><tbody>
          ${d.monsters.map(m => `<tr class="${m.boss ? 'boss' : ''}"><td>${dgMonName(m)}${m.boss ? ' <span class="egg-tag lv5">บอส</span>' : ''}</td><td>${m.level || '-'}</td><td class="dg-hp">${m.hp ? fmtNum(m.hp) : '-'}</td></tr>`).join('')}
        </tbody></table></div>` : '<div class="muted">ไฟล์เกมไม่ได้เก็บรายชื่อมอนของดันนี้ (มอนเกิดจากสคริปต์ฝั่งเซิร์ฟเวอร์)</div>'}
      </div>
      <div class="dg-grid">
        <div class="panel">
          <h4>ไอเทมที่ได้ในดันเจี้ยน <span>ตามที่เกมแสดง</span></h4>
          ${d.obtainable.length ? `<div class="jq-wrap">${d.obtainable.map(i => dgItem(i)).join('')}</div>` : '<div class="muted">ไม่มีข้อมูลไอเทมดรอปในไฟล์เกม</div>'}
        </div>
        <div class="panel">
          <h4><img src="/images/ui/ui_ach.png" class="btn-game-icon" alt=""> รางวัลเมื่อเคลียร์</h4>
          ${d.clear_reward.length ? `<div class="jq-wrap">${d.clear_reward.map(i => dgItem(i)).join('')}</div>` : '<div class="muted">ไม่มีรางวัลเคลียร์แยก (ได้จากดรอป / เควส)</div>'}
        </div>
      </div>
      ${d.quests.length ? `<div class="panel">
        <h4><img src="/images/ui/ui_quest.png" class="btn-game-icon" alt=""> เควสที่ให้กำจัดมอนในดันนี้ <span>ทำเสร็จแล้วได้ไอเทม</span></h4>
        <div class="dg-quests">${d.quests.map(q => `
          <div class="dg-quest">
            <div class="jq-title">${esc(q.title)}${q.line ? ` <small class="muted">· ${esc(q.line)}</small>` : ''}</div>
            ${q.start_npc ? `<div class="jq-npc">รับเควส: ${dgNpc(q.start_npc)}</div>` : ''}
            <div class="jq-npc">${q.defeat.map(m => `กำจัด ${dgMonName(m)} ×${m.count}`).join(' · ')}</div>
            <div class="jq-rew"><span class="egg-lab">รางวัล</span><span class="jq-wrap">${q.rewards.map(w => w.id ? dgItem(w) : w.exp ? `<span class="jq-item"><img src="/images/ui/ui_exp.png" class="btn-game-icon" alt="EXP"> ${fmtNum(w.exp)}</span>` : `<span class="jq-item">${fmtMoney(w.money)}</span>`).join('')}</span></div>
          </div>`).join('')}</div>
      </div>` : ''}
      ${d.exchange_npcs.length ? `<div class="panel">
        <h4>NPC แลกของ <span>ใช้ของจากดันนี้แลกได้</span></h4>
        ${d.exchange_npcs.map(exchBlock).join('')}
      </div>` : ''}
    </div>`;
}

async function loadDungeons() {
  const container = document.getElementById('dungeons-list-container');
  const mp = document.getElementById('dg-map-pills');
  if (mp && !mp.dataset.bound && !mp.innerHTML.trim()) mp.innerHTML = SKEL.pills([68, 88, 96, 82, 92]);
  if (container && !(STATE.dungeons.items || []).length) container.innerHTML = SKEL.dungeons();
  try {
    const res = await fetch('/api/dungeons');
    const data = await res.json();
    STATE.dungeons.items = data.items || [];
  } catch (err) {
    console.error('Failed to load dungeons:', err);
    STATE.dungeons.items = [];
  }
  if (mp && !mp.dataset.bound) {
    mp.dataset.bound = '1';
    const groups = dgGroups(STATE.dungeons.items);
    mp.innerHTML = `<button class="filter-pill active" data-k="all">ทุกแมพ</button>` +
      groups.map(g => `<button class="filter-pill" data-k="${esc(g.key)}">${g.icon} ${esc(g.name)} <small>${g.count}</small></button>`).join('');
  }
  ['dg-map-pills', 'dg-kind-pills'].forEach(id => {
    const el = document.getElementById(id);
    if (!el || el.dataset.wired) return;
    el.dataset.wired = '1';
    el.querySelectorAll('.filter-pill').forEach(b => b.addEventListener('click', () => {
      el.querySelectorAll('.filter-pill').forEach(x => x.classList.toggle('active', x === b));
      STATE.dungeons[id === 'dg-map-pills' ? 'map' : 'kind'] = b.dataset.k;
      renderDungeons();
    }));
  });
  renderDungeons();
}

// difficulty of a dungeon: its label, or "(ระดับง่าย)" / "(Easy)" in its name
function dgDiff(d) {
  const t = `${d.variant || ''} ${d.name}`.toLowerCase();
  if (/ง่าย|easy/.test(t)) return 0;
  if (/ยาก|hard/.test(t)) return 2;
  return 1;   // ธรรมดา / normal / no label
}
function dgBase(name) {
  return name.replace(/\s*[\[(]\s*(ระดับ[^\])]*|easy|normal|hard)\s*[\])]/ig, '').replace(/\s+/g, ' ').trim();
}
// easiest / lowest level first; dungeons of one name stay together (ง่าย -> ธรรมดา -> ยาก)
function dgSort(list) {
  const lowest = {};
  list.forEach(d => { const b = dgBase(d.name); lowest[b] = Math.min(lowest[b] ?? 1e9, d.level || 0); });
  return list.sort((a, b) => {
    const ba = dgBase(a.name), bb = dgBase(b.name);
    return (lowest[ba] - lowest[bb]) || ba.localeCompare(bb, 'th') || (dgDiff(a) - dgDiff(b)) || ((a.level || 0) - (b.level || 0));
  });
}

// map (where the entry NPC stands) -> NPCs on that map -> their dungeons
const DG_FIRST_MAPS = [3, 2];   // ศูนย์บัญชาการ DATS, D-เทอร์มินัล first
function dgGroups(items) {
  const groups = {};
  const add = (key, name, icon, order, npcKey, npc, d) => {
    const g = groups[key] = groups[key] || { key, name, icon, order, npcs: {}, ids: new Set() };
    const n = g.npcs[npcKey] = g.npcs[npcKey] || { npc, dungeons: [] };
    if (!n.dungeons.includes(d)) n.dungeons.push(d);
    g.ids.add(d.key);
  };
  items.forEach(d => {
    if (!d.instance) return add('field', 'แมพดันเจี้ยน (เดินเข้าได้เลย)', '', 9000, 'field', null, d);
    if (!d.entry_npcs.length) return add('none', 'ไม่พบ NPC ในไฟล์เกม', '', 9999, 'none', null, d);
    d.entry_npcs.forEach(n => {
      if (!n.map_id) return add('event', 'NPC กิจกรรม (ไม่ได้ยืนประจำแมพ)', '', 9500, n.id, n, d);
      const fi = DG_FIRST_MAPS.indexOf(n.map_id);
      add('m' + n.map_id, n.map, '', fi >= 0 ? fi : 100, n.id, n, d);
    });
  });
  const list = Object.values(groups);
  list.forEach(g => {
    g.count = g.ids.size;
    g.minLevel = Math.min(...[...g.ids].map(k => (items.find(x => x.key === k) || {}).level || 0));
    Object.values(g.npcs).forEach(n => dgSort(n.dungeons));
  });
  return list.sort((a, b) => a.order - b.order || a.minLevel - b.minLevel);
}

function filterDungeons() { renderDungeons(); }
function setDungeonCategory() { renderDungeons(); }

function toggleDungeon(key, uid) {
  const d = STATE.dungeons.items.find(x => x.key === key);
  const box = document.getElementById('dg-body-' + uid);
  if (!d || !box) return;
  const open = box.dataset.open === '1';
  box.dataset.open = open ? '0' : '1';
  box.innerHTML = open ? '' : dgDetail(d);
  box.parentElement.classList.toggle('open', !open);
}

let DG_UID = 0;
function dgCard(d) {
  const uid = ++DG_UID;
  const boss = d.monsters.find(m => m.boss) || d.monsters[d.monsters.length - 1];
  return `
    <div class="dg-card">
      <a class="dg-head" href="/dungeon/${encodeURIComponent(d.slug || d.name || d.key)}">
        <div class="dg-boss">${boss && boss.icon ? `<img src="${esc(boss.icon)}" alt="" onerror="this.remove()">` : ''}</div>
        <div class="dg-title">
          <div class="dg-name">${esc(d.name)}${d.variant ? ` <span class="jq-chip">${esc(d.variant)}</span>` : ''}</div>
          <div class="dg-meta">${d.instance ? 'อินสแตนซ์' : 'แมพดันเจี้ยน'}${d.players ? ` · ${d.players} คน` : ''}
            ${d.level_range.length ? ` · Lv.${d.level_range[0]}${d.level_range[1] !== d.level_range[0] ? '-' + d.level_range[1] : ''}` : ''}
            ${boss ? ` · บอส ${esc(boss.name)} (HP ${fmtNum(boss.hp)})` : ''}</div>
        </div>
        <div class="dg-badges">
          ${d.ticket ? '<span class="egg-tag">ใช้บัตร</span>' : ''}
          ${d.quests.length ? `<span class="egg-tag drop">${d.quests.length} เควส</span>` : ''}
          ${d.exchange_npcs.length ? '<span class="egg-tag lv5">แลกของ</span>' : ''}
          <span class="dg-chev">›</span>
        </div>
      </a>
    </div>`;
}

function renderDungeons() {
  const container = document.getElementById('dungeons-list-container');
  if (!container) return;
  const st = STATE.dungeons;
  const q = (document.getElementById('dungeon-search-input').value || '').trim().toLowerCase();
  const map = st.map || 'all', kind = st.kind || 'all';
  const items = (st.items || []).filter(d =>
    (kind === 'all' || (kind === 'instance' && d.instance) || (kind === 'field' && !d.instance) ||
      (kind === 'quest' && d.quests.length) || (kind === 'exchange' && d.exchange_npcs.length)) &&
    (!q || JSON.stringify([d.name, d.map, d.desc, d.monsters.map(m => m.name), d.obtainable.map(i => i.name),
    d.clear_reward.map(i => i.name), d.entry_npcs.map(n => [n.name, n.title, n.map]), d.exchange_npcs.map(n => n.name),
    d.quests.map(x => [x.title, x.rewards.map(w => w.name)])]).toLowerCase().includes(q)));
  const groups = dgGroups(items).filter(g => map === 'all' || g.key === map);
  document.getElementById('dg-count').textContent = new Set(groups.flatMap(g => [...g.ids])).size;
  if (!groups.length) {
    container.innerHTML = '<div class="empty-note">ไม่พบดันเจี้ยนที่ตรงกับเงื่อนไข</div>';
    return;
  }
  DG_UID = 0;
  container.innerHTML = groups.map(g => `
    <section class="dg-map">
      <h3 class="dg-map-h">${g.icon} ${esc(g.name)} <span>${g.key.startsWith('m') || g.key === 'event' ? `${Object.keys(g.npcs).length} NPC · ` : ''}${g.count} ดันเจี้ยน</span></h3>
      ${Object.values(g.npcs).map(n => `
        <div class="dg-npc-block">
          ${n.npc ? `<div class="dg-npc-h">${dgNpcPic(n.npc, true)}<div><b>${esc(n.npc.name)}</b>${n.npc.title ? ` <small class="muted">&lt;${esc(n.npc.title)}&gt;</small>` : ''}
            <div class="dg-meta">พาเข้า ${n.dungeons.length} ดันเจี้ยน</div></div></div>` : ''}
          <div class="dg-list">${n.dungeons.map(dgCard).join('')}</div>
        </div>`).join('')}
    </section>`).join('');
}

// ==========================================
// 6. CURRENCY CALCULATOR LOGIC
// ==========================================
function initCurrencyCalculator() {
  updateAllCurrencyCalculations();
}

function onTeraInput() {
  const teraInput = document.getElementById('calc-tera-input');
  const thbInput = document.getElementById('calc-thb-input');
  if (!teraInput || !thbInput) return;

  const teraVal = parseFloat(teraInput.value) || 0;
  const thbVal = teraVal * STATE.currencyRate;
  thbInput.value = thbVal.toFixed(2);

  updateUnits(teraVal);
}

function onThbInput() {
  const teraInput = document.getElementById('calc-tera-input');
  const thbInput = document.getElementById('calc-thb-input');
  if (!teraInput || !thbInput) return;

  const thbVal = parseFloat(thbInput.value) || 0;
  const teraVal = STATE.currencyRate > 0 ? (thbVal / STATE.currencyRate) : 0;
  teraInput.value = teraVal.toFixed(2);

  updateUnits(teraVal);
}

function updateUnits(teraVal) {
  const megaEl = document.getElementById('calc-mega-display');
  const bitEl = document.getElementById('calc-bit-display');

  const megaVal = teraVal * 1000;
  const bitVal = teraVal * 1000000;

  if (megaEl) megaEl.textContent = `${megaVal.toLocaleString()} M`;
  if (bitEl) bitEl.textContent = `${bitVal.toLocaleString()} B`;
}

function setPresetTera(val) {
  const teraInput = document.getElementById('calc-tera-input');
  if (teraInput) {
    teraInput.value = val;
    onTeraInput();
  }
}

function adjustRate(delta) {
  let newRate = Math.round((STATE.currencyRate + delta) * 100) / 100;
  if (newRate < 0.05) newRate = 0.05;
  setRate(newRate);
}

function resetRate() {
  setRate(0.55);
}

function onCustomRateChange() {
  const input = document.getElementById('custom-rate-input');
  if (input) {
    const val = parseFloat(input.value);
    if (!isNaN(val) && val > 0) {
      setRate(val);
    }
  }
}

function setRate(rate) {
  STATE.currencyRate = Math.round(rate * 100) / 100;

  const rateText = document.getElementById('current-rate-text');
  const headerRate = document.getElementById('header-rate-display');
  const customInput = document.getElementById('custom-rate-input');

  if (rateText) rateText.textContent = STATE.currencyRate.toFixed(2);
  if (headerRate) headerRate.textContent = STATE.currencyRate.toFixed(2);
  if (customInput && document.activeElement !== customInput) {
    customInput.value = STATE.currencyRate.toFixed(2);
  }

  updateAllCurrencyCalculations();
}

function updateAllCurrencyCalculations() {
  onTeraInput();

  const presets = [50, 100, 500, 1000, 2000, 5000, 10000, 20000];
  presets.forEach(p => {
    const el = document.getElementById(`p-${p}`);
    if (el) {
      const thb = (p * STATE.currencyRate).toLocaleString();
      el.textContent = `${thb} ฿`;
    }
  });
}


// ==========================================
// 1b. DIGIEGG (DIGITAMA) CATALOGUE
// ==========================================
const EGG_STATE = { items: null, src: 'all', type: 'all' };
const EGG_SRC = [
  ['all', 'ทั้งหมด'], ['drop', 'ดรอปตามแมพ'], ['nodrop', 'ไม่ดรอปตามแมพ'],
  ['mall', 'ไข่มอลล์'], ['jogress', 'ไข่โจเกรส'], ['lv3', '3/5'], ['lv4', '4/5'], ['lv5', '5/5'],
  ['spirit', 'สปิริตทั้งหมด'], ['spirit-norm', 'สปิริตธรรมดา'], ['spirit-high', 'สปิริต H']
];
const EGG_TYPE_TH = {
  Beast: 'สัตว์', Dragon: 'มังกร', Bird: 'นก', Aquatic: 'สัตว์น้ำ', Insectoid: 'แมลง',
  Plant: 'พืช', Devil: 'ปีศาจ', Rock: 'หิน', Fire: 'ไฟ', Mutant: 'กลายพันธุ์'
};

function showDexView(view) {
  const eggs = view === 'eggs';
  const jog = view === 'jogress';
  const dk = view === 'decks';
  const seals = view === 'seals';
  const dunits = view === 'dunits';
  document.getElementById('dex-view-eggs').style.display = eggs ? '' : 'none';
  document.getElementById('dex-view-jogress').style.display = jog ? '' : 'none';
  document.getElementById('dex-view-decks').style.display = dk ? '' : 'none';
  document.getElementById('dex-view-seals').style.display = seals ? '' : 'none';
  const duView = document.getElementById('dex-view-dunits');
  if (duView) duView.style.display = dunits ? '' : 'none';
  document.getElementById('dex-view-digimon').style.display = (eggs || jog || dk || seals || dunits) ? 'none' : '';
  document.getElementById('dex-sw-eggs').classList.toggle('active', eggs);
  document.getElementById('dex-sw-jogress').classList.toggle('active', jog);
  document.getElementById('dex-sw-decks').classList.toggle('active', dk);
  document.getElementById('dex-sw-seals').classList.toggle('active', seals);
  const duSw = document.getElementById('dex-sw-dunits');
  if (duSw) duSw.classList.toggle('active', dunits);
  document.getElementById('dex-sw-digimon').classList.toggle('active', !eggs && !jog && !dk && !seals && !dunits);
  if (eggs) return loadEggs();
  if (dunits) return loadDUnits();
}

async function loadEggs() {
  if (!EGG_STATE.items) {
    const src = document.getElementById('egg-src-pills');
    const tp = document.getElementById('egg-type-pills');
    if (src && !src.innerHTML.trim()) src.innerHTML = SKEL.pills([66, 84, 78, 86]);
    if (tp && !tp.innerHTML.trim()) tp.innerHTML = SKEL.pills([66, 76, 82, 74, 80, 72]);
    document.getElementById('egg-grid').innerHTML = SKEL.eggs(10);
    try { EGG_STATE.items = await (await fetch('/api/eggs')).json(); } catch (e) { EGG_STATE.items = []; }
    src.innerHTML = EGG_SRC.map(([k, l]) => `<button class="filter-pill${k === 'all' ? ' active' : ''}" data-k="${k}">${l}</button>`).join('');
    bindEggPills(src, k => { EGG_STATE.src = k; });
    const types = [...new Set(EGG_STATE.items.map(e => e.data_type).filter(Boolean))].sort();
    tp.innerHTML = `<button class="filter-pill active" data-k="all">ทุกหมวด</button>` + types.map(t => {
      const ic = (EGG_STATE.items.find(e => e.data_type === t && e.egg_icon) || {}).egg_icon;
      return `<button class="filter-pill icon-pill" data-k="${esc(t)}">${ic ? `<img src="${esc(ic)}" alt="">` : ''}ไข่${esc(EGG_TYPE_TH[t] || t)}</button>`;
    }).join('') + `<button class="filter-pill" data-k="none">ไม่ระบุดาต้า</button>`;
    bindEggPills(tp, k => { EGG_STATE.type = k; });
  }
  renderEggs();
}

function bindEggPills(container, onPick) {
  container.querySelectorAll('.filter-pill').forEach(b => b.addEventListener('click', () => {
    container.querySelectorAll('.filter-pill').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    onPick(b.dataset.k);
    renderEggs();
  }));
}

function eggTitle(e) {
  const name = esc(e.thai_name || e.title);
  return e.line ? `${name} <small class="egg-line">สาย ${esc(e.line_th || e.line)}</small>` : name;
}

function eggTags(e) {
  const t = [];
  if (e.spirit) {
    if (e.spirit_info && e.spirit_info.hyper) {
      t.push('<span class="egg-tag spirit-high">สปิริต H</span>');
    } else {
      t.push('<span class="egg-tag spirit-norm">สปิริตธรรมดา</span>');
    }
  } else {
    if (e.drops && e.drops.length) t.push('<span class="egg-tag drop">ดรอปตามแมพ</span>');
    else t.push('<span class="egg-tag nodrop">ไม่ดรอปตามแมพ</span>');
    if (e.is_jogress) {
      t.push('<span class="egg-tag jogress-badge">ไข่โจเกรส</span>');
      t.push('<span class="egg-tag lv lv4">โจเกรส 4/5</span>');
      t.push('<span class="egg-tag lv lv5">โจเกรส 5/5</span>');
    } else {
      t.push('<span class="egg-tag lv lv3">มอลล์ 3/5</span>');
      t.push('<span class="egg-tag lv lv4">มอลล์ 4/5</span>');
      t.push('<span class="egg-tag lv lv5">มอลล์ 5/5</span>');
    }
  }
  return t.join('');
}

function spiritReq(e, big = false) {
  const si = e.spirit_info || {};
  const frameCls = si.frame_color === 'purple' ? 'frame-purple' : 'frame-blue';
  const it = (icon, th, en, extraCls = '') => `<span class="spirit-req${big ? ' big' : ''}">${icon ? `<img class="${extraCls}" src="${esc(icon)}" alt="">` : ''}${esc(th)}${big && en ? ` <small class="en">${esc(en)}</small>` : ''}</span>`;
  let moneyHtml = '';
  if (si.hyper && si.money_cost) {
    moneyHtml = `<span class="plus">+</span><span class="spirit-req${big ? ' big' : ''} money-tera"><img class="tera-icon" src="${esc(si.money_icon)}" alt="T"> <b>${esc(si.money_cost)}</b></span>`;
  }
  return `<span class="spirit-reqs">${it(si.item_icon, si.item_th, '', frameCls)}<span class="plus">+</span>${it(si.book_icon, big ? si.book_th : 'สารานุกรมโบโคมอน', '')}${moneyHtml}</span>`;
}

function eggChain(e, small) {
  if (!e.chain || !e.chain.length) return '';
  const head = { slug: e.slug, name: e.thai_name || e.title, icon: e.icon || e.image, jogress: false };
  const list = small ? e.chain.slice(0, 4) : e.chain;
  const cell = m => {
    const inner = `<img src="${esc(m.icon || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'"><span>${esc(m.name)}</span>${m.jogress ? '<em>โจเกรส</em>' : ''}`;
    return small ? `<span class="egg-evo${m.jogress ? ' jog' : ''}">${inner}</span>`
      : `<a class="egg-evo${m.jogress ? ' jog' : ''}" href="${m.slug ? digiHref(m.slug) : '#'}" onclick="${m.slug ? 'closeEgg(true)' : 'return false'}">${inner}</a>`;
  };
  return `<div class="egg-chain${small ? ' sm' : ''}">${[head, ...list].map(cell).join('<span class="egg-evo-arrow">›</span>')}${small && e.chain.length > 4 ? '<span class="egg-evo-more">…</span>' : ''}</div>`;
}

function eggIcon(e, cls = 'egg-ic') {
  if (e.spirit && e.spirit_info && e.spirit_info.item_icon) {
    const frameCls = e.spirit_info.frame_color === 'purple' ? 'frame-purple' : 'frame-blue';
    return `<img class="${cls} ${frameCls}" src="${esc(e.spirit_info.item_icon)}" alt="${esc(e.spirit_info.item)}" title="${esc(e.spirit_info.item_th || e.spirit_info.item)} (${esc(e.spirit_info.type_th || '')})">`;
  }
  if (e.egg_icon) return `<img class="${cls}" src="${esc(e.egg_icon)}" alt="ไข่" title="${esc(e.data_type)} Mercenary DigiEgg">`;
  return `<span class="${cls} ph"></span>`;
}

function eggKind(e) {
  if (e.spirit && e.spirit_info && e.spirit_info.hyper) return `สปิริตขั้นสูง (H) · รวม 10 ชิ้น`;
  if (e.spirit && e.spirit_info) return `สปิริตธรรมดา · ธาตุ${esc(e.spirit_info.elem_th || '')}`;
  return e.data_type ? `ไข่${esc(e.data_th)}` : '-';
}

function eggData(e, big = false) {
  if (e.spirit) return spiritReq(e, big);
  if (!e.data_type) return '<span class="muted">dmowiki ไม่ได้ระบุดาต้า</span>';
  return `<span class="egg-data${big ? ' big' : ''}">${e.data_icon ? `<img src="${esc(e.data_icon)}" alt="">` : ''}
    ดาต้า${esc(e.data_th)} ระดับต่ำ <b>×${esc(e.data_amount)}</b> / ขั้น${big ? ` <small class="en">${esc(e.data_item)}</small>` : ''}</span>`;
}

function renderEggs() {
  const grid = document.getElementById('egg-grid');
  if (!grid || !EGG_STATE.items) return;
  const q = (document.getElementById('egg-search-input').value || '').trim().toLowerCase();
  const items = EGG_STATE.items.filter(e => {
    if (EGG_STATE.src !== 'all' && !e.tags.includes(EGG_STATE.src)) return false;
    if (EGG_STATE.type === 'none' && e.data_type) return false;
    if (!['all', 'none'].includes(EGG_STATE.type) && e.data_type !== EGG_STATE.type) return false;
    if (!q) return true;
    const hay = [e.title, e.thai_name, e.line, e.line_th, e.egg_name, e.data_type, e.data_th, `ไข่${e.data_th}`,
    e.data_type === 'Aquatic' ? 'ไข่น้ำ' : '', ...(e.aka || []), e.client_name || '', ...(e.chain || []).map(m => `${m.name} ${m.title}`),
    ...e.drops.map(d => `${d.monster} ${d.monster_th} ${d.map} ${d.map_th}`), ...e.boxes.map(b => b.box)].join(' ').toLowerCase();
    return hay.includes(q);
  });
  document.getElementById('egg-count').textContent = items.length;
  if (!items.length) { grid.innerHTML = '<div class="empty-note">ไม่พบไข่ที่ตรงกับเงื่อนไข</div>'; return; }
  grid.innerHTML = items.map(e => `
    <a class="egg-card" href="/egg/${encodeURIComponent(e.key)}">
      <div class="egg-card-top">
        <div class="egg-icons">
          ${(e.spirit && e.spirit_info && e.spirit_info.hyper)
      ? `<img class="egg-digi hyper-digi" src="${esc(e.icon || e.image || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">`
      : `${eggIcon(e)}<span class="egg-arrow">&rarr;</span><img class="egg-digi" src="${esc(e.icon || e.image || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">`
    }
        </div>
        <div class="egg-name">${eggTitle(e)}</div>
        <div class="egg-en">${esc(e.spirit ? e.title + ' · ' + (e.spirit_info || {}).item : e.egg_name)}</div>
      </div>
      <div class="egg-row"><span class="egg-lab">${e.spirit ? 'ประเภท' : 'หมวดไข่'}</span><span>${eggKind(e)}</span></div>
      <div class="egg-row"><span class="egg-lab">ใช้ฟัก</span>${eggData(e)}</div>
      ${e.spirit ? '' : eggChain(e, true)}
      <div class="egg-tags">${eggTags(e)}</div>
    </a>`).join('');
}

function openEgg(key) {
  const show = () => {
    const e = (EGG_STATE.items || []).find(x => x.key === key) || (EGG_STATE.items || []).find(x => x.slug === key);
    if (!e) {
      showNotFoundPage('egg/' + key, `ไม่พบข้อมูลไข่ "${key}" ในระบบ`);
      return;
    }
    const m = document.getElementById('egg-modal');
    const box = document.getElementById('egg-modal-box');
    const lvTh = lv => `ใส่ดาต้ามาแล้ว ${lv} ขั้น` + (lv === 5 ? ' (ขนาดใหญ่สุด)' : '');
    box.innerHTML = `
      <button class="egg-close" onclick="closeEgg()" title="ปิด">&times;</button>
      <div class="egg-head">
        ${(e.spirit && e.spirit_info && e.spirit_info.hyper)
        ? `<img class="egg-digi big hyper-digi" src="${esc(e.icon || e.image || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">`
        : eggIcon(e, 'egg-ic big')
      }
        <div>
          <h2>${eggTitle(e)}</h2>
          <div class="egg-en">${esc(e.spirit ? e.title + ' · ' + (e.spirit_info || {}).item : e.egg_name)}</div>
          <div class="egg-tags">${eggTags(e)}</div>
        </div>
      </div>
      <div class="egg-detail-grid">
        <div class="panel">
          <h3 class="panel-title">ฟักออกมาเป็น</h3>
          <a class="egg-digi-link" href="${digiHref(e.slug)}" onclick="closeEgg(true)">
            <img src="${esc(e.icon || e.image || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">
            <div><strong>${esc(e.thai_name || e.title)}</strong><br><small class="en">${esc(e.title)} · ${esc(e.form_th || e.form)}</small></div>
          </a>
          ${e.line ? `<div class="egg-row" style="margin-top:8px"><span class="egg-lab">สายวิวัฒนาการ</span>
            ${e.line_slug ? `<a href="${digiHref(e.line_slug)}" onclick="closeEgg(true)">${e.line_icon ? `<img class="ib-icon" src="${esc(e.line_icon)}" alt="">` : ''}${esc(e.line_th || e.line)}</a>` : esc(e.line_th || e.line)}
            <small class="en">${esc(e.line)}${(e.aka || []).length ? ' / ' + esc(e.aka.join(' / ')) : ''}</small></div>` : ''}
          ${e.spirit ? '' : `<div class="egg-row"><span class="egg-lab">หมวดไข่</span><span>${e.data_type ? `ไข่${esc(e.data_th)} <small class="en">${esc(e.data_type)} Mercenary DigiEgg</small>` : '-'}</span></div>
          <div class="egg-row"><span class="egg-lab">ดาต้าที่ใช้ฟัก</span>${eggData(e, true)}</div>`}
          ${e.data_type ? '<div class="egg-hint">ต้องใส่ดาต้าอย่างน้อย 3 ขั้นถึงจะฟักได้ แต่ละขั้นมีโอกาสล้มเหลว (ใช้ Hatch Backup กันไข่แตก)</div>' : ''}
          ${e.chain && e.chain.length ? `<div class="egg-row" style="margin-top:10px"><span class="egg-lab">วิวัฒนาการสายนี้</span></div>${eggChain(e)}` : ''}
          ${e.hatch_shot ? `<img class="egg-shot" src="${esc(e.hatch_shot)}" alt="หน้าจอฟักไข่" onerror="this.style.display='none'">` : ''}
        </div>
        <div>
          ${e.spirit ? spiritPanel(e) : ''}
          <div class="panel"${e.spirit ? ' style="display:none"' : ''}>
            <h3 class="panel-title">ดรอปตามแมพ <span>${e.drops.length ? `${e.drops.length} จุด` : ''}</span></h3>
            ${e.drops.length ? `<div class="table-responsive"><table class="custom-table"><thead><tr><th>มอนที่ดรอป</th><th>แมพ</th><th>เลเวล</th></tr></thead><tbody>
              ${e.drops.map(d => `<tr>
                <td>${d.monster_slug ? `<a href="${digiHref(d.monster_slug)}" onclick="closeEgg(true)">${esc(d.monster_th || d.monster)}</a>` : esc(d.monster_th || d.monster)}${d.monster_th ? ` <small class="en">${esc(d.monster)}</small>` : ''}</td>
                <td>${esc(d.map_th || d.map)}${d.map_th ? ` <small class="en">${esc(d.map)}</small>` : ''}</td>
                <td>${esc(d.levels)}</td></tr>`).join('')}
              </tbody></table></div>`
        : `<div class="muted">${e.spirit ? 'ได้จากระบบสปิริต ไม่ได้ดรอปเป็นไข่' : 'ไข่ใบนี้ไม่มีดรอปตามแมพ ได้จากมอลล์ อีเวนต์ หรือเควสเท่านั้น'}</div>`}
          </div>
          <div class="panel"${e.spirit ? ' style="display:none"' : ''}>
            <h3 class="panel-title"><img src="/images/ui/ui_shop.png" class="btn-game-icon" alt=""> ไข่มอลล์ / อีเวนต์ <span>${e.is_jogress ? 'ไข่โจเกรสเสริมพลัง (Lv.4 · Lv.5)' : 'ไข่เสริมพลัง (3/5 · 4/5 · 5/5)'}</span></h3>
            ${(e.mall_eggs && e.mall_eggs.length) ? `<div class="egg-boxes">${e.mall_eggs.map(b => `
              <div class="egg-box ${b.is_jogress ? 'egg-box-jogress' : ''}">
                <img src="${esc(b.icon)}" alt="" style="width:44px; height:44px; object-fit:contain; border-radius:8px;" onerror="this.src='/images/client_items/egg_reinforced_lv5_universal.png'">
                <div style="flex:1">
                  <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
                    <strong style="color:${b.is_jogress ? '#d8b4fe' : '#f8fafc'}; font-size:0.88rem;">${esc(b.name_th)}</strong>
                    <span class="egg-tag ${esc(b.tag_class || 'lv')}">${esc(b.tag)}</span>
                  </div>
                  <div class="muted" style="font-size:0.75rem; margin-top:2px;">${esc(b.name_en)}</div>
                  <div style="font-size:0.78rem; color:#94a3b8; margin-top:4px; line-height:1.35;">${esc(b.desc)}</div>
                </div>
              </div>`).join('')}</div>
              <div class="egg-hint"><strong>ไข่เสริมพลัง</strong>: ใส่ดาต้ามาให้แล้ว การันตีฟักสำเร็จ 100% ไม่ต้องลุ้นและไม่ต้องใช้ Hatch Backup</div>`
        : '<div class="muted">ไม่มีข้อมูลไข่มอลล์</div>'}
          </div>
        </div>
      </div>`;
    m.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  };
  if (EGG_STATE.items) show(); else loadEggs().then(show);
}

function closeEgg(silent) {
  const m = document.getElementById('egg-modal');
  if (m) m.style.display = 'none';
  document.body.style.overflow = '';
  if (!silent && getRoutePath().startsWith('egg/')) navigateTo('eggs');
}
document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeEgg(); });


function spiritPanel(e) {
  const si = e.spirit_info || {};
  const row = (icon, th, en, note, extraCls = '') => `
    <div class="egg-box">${icon ? `<img class="${extraCls}" src="${esc(icon)}" alt="">` : ''}
      <div><strong>${esc(th)}</strong>${en ? ` <small class="en">${esc(en)}</small>` : ''}${note ? `<div class="muted" style="font-size:.76rem">${note}</div>` : ''}</div></div>`;
  if (si.hyper) return `
    <div class="panel">
      <h3 class="panel-title">วิธีปลดสปิริตขั้นสูง (H) <span>ที่ NPC ${esc(si.npc_th)} (${esc(si.npc_map_th)})</span></h3>
      <div class="egg-boxes">
        ${row(si.npc_icon, 'คุยกับ ' + si.npc_th, si.npc, 'NPC อยู่ที่ศูนย์บัญชาการ DATS')}
        <div class="egg-box" style="align-items:flex-start"><div style="width:100%">
          <strong>สปิริตขั้นสูง (H) ครบ 10 ชิ้น (ฮิวแมนและบีสต์ของธาตุ${esc((si.elems_th || []).join(', '))})</strong>
          <div class="shining-grid">${(si.shinings || []).map(x => `
            <div class="shining-item" title="${esc(x.item_th)}">
              <img class="frame-purple" src="${esc(x.icon)}" alt="">
              <span>${esc(x.item_th)}</span>
            </div>`).join('')}</div>
          <div class="muted" style="font-size:.76rem;margin-top:8px"><b>วิธีได้สปิริต (H):</b> เลี้ยงสปิริตตัวธรรมดาแต่ละตัวจนถึง Lv.99 แล้วนำไปแลกเปลี่ยนเป็น "สปิริตขั้นสูง (H)" ที่โบโคมอน (ดิจิมอนตัวนั้นจะหายไป) หรือเปิดจากกล่อง/ไข่สุ่มสปิริตขั้นสูง</div>
        </div></div>
        ${row(si.book_icon, si.book_th + ' ×1', 'ไอเทมรหัส 99100', 'ไอเทมสำคัญจาก Cash Shop หรือกิจกรรม')}
        <div class="egg-box">
          <img class="tera-icon-box" src="${esc(si.money_icon)}" alt="T">
          <div>
            <strong>ค่าปลดที่โบโคมอน: ${esc(si.money_th || '1 T (1,000 M)')}</strong>
            <div class="muted" style="font-size:.76rem;margin-top:2px">
              จ่ายค่าธรรมเนียมตอนกดปลดร่างที่ NPC โบโคมอนจำนวน <b>1 T</b> <span style="color:#94a3b8">(${esc(si.money_total_th || 'หากรวมค่าแลกสปิริต 10 ชิ้น ชิ้นละ 500M จะเป็น 5 T + ค่าปลด 1 T รวมต้นทุนทั้งหมด 6 T')})</span>
            </div>
          </div>
        </div>
      </div>
      <div class="egg-hint">ได้ออกมาเป็นร่าง 3/5 · เมื่อเลี้ยงไคเซอร์เกรย์มอนและแมคนาการูรูมอนถึง Lv.99 ทั้งคู่ จะสามารถรวมร่างเป็น <b>ซูซาโนโอมอน (Susanoomon)</b> ได้ (เทมเมอร์ Lv.90 ขึ้นไป)</div>
    </div>`;
  return `
    <div class="panel">
      <h3 class="panel-title">วิธีฟักสปิริตธรรมดา <span>ที่ NPC ${esc(si.npc_th)} (${esc(si.npc_map_th)})</span></h3>
      <div class="egg-boxes">
        ${row(si.npc_icon, 'คุยกับ ' + si.npc_th, si.npc, 'NPC อยู่ที่ศูนย์บัญชาการ DATS')}
        <div class="egg-box">
          <img class="frame-blue" src="${esc(si.item_icon)}" alt="">
          <div>
            <strong>${esc(si.item_th)} ×1</strong>
            <div class="muted" style="font-size:.76rem;margin-top:2px">
              ไอเทมระดับธรรมดา · ดรอปจากบอสที่เรียกด้วย ${esc(si.card_th)} (การ์ดดรอปจากมอนสเตอร์ธาตุ${esc(si.elem_th || si.elem)})
            </div>
          </div>
        </div>
        ${row(si.book_icon, si.book_th + ' ×1', 'ไอเทมรหัส 99100', 'ไอเทมสำคัญจาก Cash Shop หรือกิจกรรม')}
      </div>
      <div class="egg-hint">
        <b>สำคัญ:</b> สปิริตทั้ง 20 ตัวนี้ <u>ใช้สปิริตระดับธรรมดาเท่านั้น ไม่ใช้สปิริต H</u> · ฟักออกมาเป็นร่าง 3/5 ทันที (ไม่มีค่าธรรมเนียมเงิน Tera)<br>
        เมื่อเลี้ยงสปิริตตัวนี้จนถึง <b>Lv.99</b> สามารถนำไปแลกเป็น <b>${esc(si.shining)}</b> ที่โบโคมอนได้ (เสียค่าธรรมเนียม 500 M) เพื่อใช้ปลดร่าง ไคเซอร์เกรย์มอน หรือ แมคนาการูรูมอน ต่อไป
      </div>
    </div>`;
}


// ==========================================
// THAI PATCH NOTES (full offline copy of vplay.in.th)
// ==========================================
const PATCH_STATE = { items: null, kind: 'all', year: 'all' };
const PATCH_KIND = [['all', 'ทั้งหมด'], ['update', 'รายละเอียดการอัพเดท'], ['coming', 'Coming Soon'], ['fix', 'แก้ไข'], ['other', 'อื่นๆ']];
const TH_MONTH = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];

function thDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
  return m ? `${+m[3]} ${TH_MONTH[+m[2] - 1]} ${+m[1] + 543}` : (iso || '-');
}

async function refreshPatchSyncStatus() {
  const el = document.getElementById('patch-sync-status');
  if (!el) return;
  try {
    const st = await (await fetch('/api/patches/status')).json();
    const parts = ['อัปเดตอัตโนมัติทุก ' + Math.round((st.interval_sec || 1800) / 60) + ' นาที'];
    if (st.last_check) parts.push('เช็คล่าสุด ' + st.last_check);
    el.textContent = parts.join(' · ');
    if (PATCH_STATE.items && st.total && st.total !== PATCH_STATE.items.length) {
      PATCH_STATE.items = null;
      await loadPatches(true);
    }
  } catch (e) { }
}

async function loadPatches(forceReload = false) {
  if (PATCH_STATE.items && !forceReload) { renderPatchList(); refreshPatchSyncStatus(); return; }
  const list = document.getElementById('patch-list');
  const kp = document.getElementById('patch-kind-pills');
  const yp = document.getElementById('patch-year-pills');
  if (kp && !kp.innerHTML.trim()) kp.innerHTML = SKEL.pills([64, 86, 94, 72, 78]);
  if (yp && !yp.innerHTML.trim()) yp.innerHTML = SKEL.pills([58, 60, 60, 60]);
  if (list && !forceReload) list.innerHTML = SKEL.patches(8);
  try { PATCH_STATE.items = (await (await fetch('/api/patches')).json()).items || []; } catch (e) { PATCH_STATE.items = []; }
  kp.innerHTML = PATCH_KIND.filter(([k]) => k === 'all' || PATCH_STATE.items.some(a => a.kind === k))
    .map(([k, l]) => `<button class="filter-pill${k === 'all' ? ' active' : ''}" data-k="${k}">${l}</button>`).join('');
  const years = [...new Set(PATCH_STATE.items.map(a => (a.date_iso || '').slice(0, 4)).filter(Boolean))].sort().reverse();
  yp.innerHTML = `<button class="filter-pill active" data-k="all">ทุกปี</button>` +
    years.map(y => `<button class="filter-pill" data-k="${y}">${+y + 543}</button>`).join('');
  [[kp, k => { PATCH_STATE.kind = k; }], [yp, k => { PATCH_STATE.year = k; }]].forEach(([c, fn]) =>
    c.querySelectorAll('.filter-pill').forEach(b => b.addEventListener('click', () => {
      c.querySelectorAll('.filter-pill').forEach(x => x.classList.remove('active'));
      b.classList.add('active'); fn(b.dataset.k); renderPatchList();
    })));
  renderPatchList();
  refreshPatchSyncStatus();
}

function renderPatchList() {
  const list = document.getElementById('patch-list');
  if (!list || !PATCH_STATE.items) return;
  const q = (document.getElementById('patch-search-input').value || '').trim().toLowerCase();
  const items = PATCH_STATE.items.filter(a =>
    (PATCH_STATE.kind === 'all' || a.kind === PATCH_STATE.kind) &&
    (PATCH_STATE.year === 'all' || (a.date_iso || '').startsWith(PATCH_STATE.year)) &&
    (!q || `${a.title} ${(a.digimon || []).join(' ')} ${a.search || ''}`.toLowerCase().includes(q)));
  document.getElementById('patch-count').textContent = items.length;
  if (!items.length) { list.innerHTML = '<div class="empty-note">ไม่พบแพตช์ที่ตรงกับเงื่อนไข</div>'; return; }
  const snippet = a => {
    if (!q) return '';
    const t = a.search || ''; const i = t.toLowerCase().indexOf(q);
    if (i < 0) return '';
    return `<div class="patch-snip">…${esc(t.slice(Math.max(0, i - 50), i))}<mark>${esc(t.slice(i, i + q.length))}</mark>${esc(t.slice(i + q.length, i + q.length + 70))}…</div>`;
  };
  list.innerHTML = items.map(a => `
    <a class="patch-item" href="/patch/${encodeURIComponent(a.id)}">
      <div class="patch-date">${esc(thDate(a.date_iso))}</div>
      <div class="patch-main">
        <div class="patch-title"><span class="patch-kind k-${esc(a.kind)}">${esc((PATCH_KIND.find(k => k[0] === a.kind) || ['', a.kind])[1])}</span>${esc(a.title)}</div>
        ${(a.digimon || []).length ? `<div class="patch-digi"><img src="/images/ui/ui_digimon.png" class="btn-game-icon" alt=""> ${a.digimon.map(n => esc(n)).join(' · ')}</div>` : ''}
        ${snippet(a)}
      </div>
    </a>`).join('');
}

async function openPatch(id) {
  const seq = ++REQ_SEQ.patch;
  const view = document.getElementById('patch-read-view');
  document.getElementById('patch-list-view').style.display = 'none';
  view.style.display = '';
  view.innerHTML = SKEL.patchArticle();
  if (!PATCH_STATE.items) await loadPatches();
  try {
    const r = await fetch(`/api/patches/${encodeURIComponent(id)}`);
    if (!r.ok) throw new Error(r.status);
    const a = await r.json();
    if (seq !== REQ_SEQ.patch) return;
    const idx = PATCH_STATE.items.findIndex(x => x.id === id);
    const newer = idx > 0 ? PATCH_STATE.items[idx - 1] : null;
    const older = idx >= 0 && idx < PATCH_STATE.items.length - 1 ? PATCH_STATE.items[idx + 1] : null;
    const nav = `<div class="patch-nav">
        ${older ? `<a class="preset-btn" href="/patch/${encodeURIComponent(older.id)}">← ฉบับก่อนหน้า</a>` : '<span></span>'}
        <a class="preset-btn" href="/patches" onclick="event.preventDefault(); closePatch(); navigateTo('patches')">รายการแพตช์ทั้งหมด</a>
        ${newer ? `<a class="preset-btn" href="/patch/${encodeURIComponent(newer.id)}">ฉบับใหม่กว่า →</a>` : '<span></span>'}
      </div>`;
    view.innerHTML = `
      ${nav}
      <article class="panel patch-article">
        <div class="patch-head">
          <span class="patch-kind k-${esc(a.kind)}">${esc((PATCH_KIND.find(k => k[0] === a.kind) || ['', a.kind])[1])}</span>
          <h1>${esc(a.title)}</h1>
          <div class="muted">${esc(thDate(a.date_iso))} · ที่มา: <a href="${esc(a.url)}" target="_blank" rel="noopener">vplay.in.th</a></div>
        </div>
        <div class="patch-body">${a.html}</div>
      </article>
      ${nav}`;
    window.scrollTo({ top: 0 });
  } catch (e) {
    view.innerHTML = `<div class="empty-note">ไม่พบแพตช์นี้ <a href="/patches" onclick="event.preventDefault(); closePatch(); navigateTo('patches')">กลับไปรายการ</a></div>`;
  }
}

function closePatch(silent) {
  const lv = document.getElementById('patch-list-view');
  const rv = document.getElementById('patch-read-view');
  if (lv) lv.style.display = '';
  if (rv) { rv.style.display = 'none'; rv.innerHTML = ''; }
  if (!silent && getRoutePath().startsWith('patch/')) navigateTo('patches');
}


// ==========================================
// 1c. JOGRESS QUESTS (from the Thai client quest tables)
// ==========================================
const JQ_STATE = { items: null, rank: 'all' };

async function loadJogressQuests() {
  if (!JQ_STATE.items) {
    const rp = document.getElementById('jq-rank-pills');
    if (rp && !rp.innerHTML.trim()) rp.innerHTML = SKEL.pills([66, 62, 62, 58, 66]);
    const grid = document.getElementById('jq-grid');
    if (grid) grid.innerHTML = SKEL.eggs(8);
    try { JQ_STATE.items = await (await fetch('/api/jogress-quests')).json(); } catch (e) { JQ_STATE.items = []; }
    renderJogressRankPills();
  }
  renderJogressList();
}

function renderJogressRankPills() {
  const el = document.getElementById('jq-rank-pills');
  if (!el) return;
  const ranks = {};
  JQ_STATE.items.forEach(g => {
    const k = g.rank || 'none';
    ranks[k] = ranks[k] || { name: k, icon: g.rank_icon, w: g.rank_weight || 0, count: 0 };
    ranks[k].count++;
  });
  const list = Object.values(ranks).sort((a, b) => b.w - a.w);
  el.innerHTML = `<button class="filter-pill${JQ_STATE.rank === 'all' ? ' active' : ''}" data-val="all">ทั้งหมด <small>${JQ_STATE.items.length}</small></button>` +
    list.map(r => `<button class="filter-pill icon-pill${JQ_STATE.rank === r.name ? ' active' : ''}" data-val="${esc(r.name)}">${r.name === 'none' ? 'ไม่มี Rank'
      : `${r.icon ? iconImg(r.icon, r.name, 'pill-icon') : ''}${esc(r.name)}`} <small>${r.count}</small></button>`).join('');
  el.querySelectorAll('.filter-pill').forEach(b => b.addEventListener('click', () => {
    el.querySelectorAll('.filter-pill').forEach(x => x.classList.toggle('active', x === b));
    JQ_STATE.rank = b.dataset.val;
    renderJogressList();
  }));
}

function jqItem(it, small) {
  if (!it) return '';
  const cnt = it.count > 1 ? ` ×${it.count}` : '';
  return `<span class="jq-item${small ? ' sm' : ''}${it.unlock ? ' unlock' : ''}" title="${esc(it.name_th)}">${it.icon ? `<img src="${esc(it.icon)}" alt="" onerror="this.remove()">` : ''}${esc(it.name_th)}${cnt}</span>`;
}

function jqDigi(l) {
  if (!l) return '';
  const inner = `${l.icon ? `<img src="${esc(l.icon)}" alt="" onerror="this.remove()">` : ''}${esc(l.name)}`;
  return l.slug ? `<a class="jq-digi" href="${digiHref(l.slug)}">${inner}</a>` : `<span class="jq-digi">${inner}</span>`;
}

function jqSideName(s) {
  if (!s.partner) return 'เส้นเควส';
  return `ฝั่ง${s.partner.name}${s.variant ? ` (ชุดที่ ${s.variant})` : ''}`;
}

function jqHref(g, i) {
  return `/jogress/${encodeURIComponent(g.slug)}${i ? '/' + i : ''}`;
}

function renderJogressList() {
  const grid = document.getElementById('jq-grid');
  if (!grid || !JQ_STATE.items) return;
  const q = (document.getElementById('jq-search-input').value || '').trim().toLowerCase();
  const items = JQ_STATE.items.filter(g => JQ_STATE.rank === 'all' || (g.rank || 'none') === JQ_STATE.rank).filter(g => !q || JSON.stringify([g.title, g.thai_name, g.partners.map(p => p.name),
  g.reward_items.map(r => r.name_th), g.sides.map(s => s.quests.map(x => [x.title, x.start_npc && x.start_npc.name]))]).toLowerCase().includes(q));
  document.getElementById('jq-count').textContent = items.length;
  if (!items.length) { grid.innerHTML = '<div class="empty-note">ไม่พบเควสที่ตรงกับคำค้น</div>'; return; }
  grid.innerHTML = items.map(g => `
    <div class="jq-card" onclick="navigateTo('${jqHref(g, 0)}')">
      <div class="jq-card-top">
        <img class="jq-portrait" src="${esc(g.icon || g.image || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">
        <div>
          <div class="jq-name">${esc(g.thai_name)} ${g.rank ? `<span class="jq-rank" style="color:${esc(g.rank_color)}">${esc(g.rank)}</span>` : ''}</div>
          <div class="egg-en">${esc(g.title)}</div>
          <div class="jq-meta"><img src="/images/ui/ui_quest.png" class="stat-icon-inline" alt=""> ${g.quest_count} เควส${g.max_tamer_level ? ` · เทมเมอร์ Lv.${g.max_tamer_level}+` : ''}${g.max_digimon_level ? ` · ดิจิมอน Lv.${g.max_digimon_level}+` : ''}</div>
        </div>
      </div>
      <div class="jq-side-list">
        ${g.sides.map((s, i) => `<a class="jq-side-row" href="${jqHref(g, i)}" onclick="event.stopPropagation()">
          ${s.partner && s.partner.icon ? `<img src="${esc(s.partner.icon)}" alt="" onerror="this.remove()">` : ''}
          <span class="jq-side-name">${esc(jqSideName(s))}${s.form ? ` <small class="muted">→ ร่าง ${esc(s.form.name)}</small>` : ''}</span>
          <span class="jq-side-count">${s.quest_count} เควส</span></a>`).join('')}
      </div>
      ${g.reward_items.length ? `<div class="jq-row"><span class="egg-lab">ได้จากเควส</span><span class="jq-wrap">${g.reward_items.map(r => jqItem(r, true)).join('')}</span></div>` : ''}
      <div class="egg-tags">
        ${g.unlocks_by_quest ? '<span class="egg-tag drop">ทำเควสครบ = ปลดร่างโจเกรส</span>' : ''}
        ${g.unlock_from_quest.length ? '<span class="egg-tag lv5">ไอเทมปลดร่างได้จากเควส</span>' : ''}
      </div>
    </div>`).join('');
}

function jqObjective(o) {
  if (o.kind === 'defeat') return `กำจัด <b>${esc(o.target)}</b> × ${o.count}`;
  if (o.kind === 'talk') return `คุยกับ <b>${esc(o.target)}</b>${o.title ? ` <small class="muted">&lt;${esc(o.title)}&gt;</small>` : ''}`;
  if (o.kind === 'collect') return `รวบรวม <b>${esc(o.target)}</b>${o.count > 1 ? ` × ${o.count}` : ''}`;
  return `${esc(String(o.target || ''))}${o.count > 1 ? ` × ${o.count}` : ''}`;
}

function jqReward(w) {
  if (w.kind === 'item') return jqItem(w.item);
  if (w.kind === 'exp') return `<span class="jq-item"><img src="/images/ui/ui_exp.png" class="btn-game-icon" alt="EXP"> ${Number(w.value).toLocaleString()}</span>`;
  if (w.kind === 'money') return `<span class="jq-item"><img src="/images/ui/ui_money.png" class="btn-game-icon" alt="เงิน"> ${Number(w.value).toLocaleString()}</span>`;
  return '';
}

function jqNpc(n) {
  return `<b>${esc(n.name)}</b>${n.title ? ` <small class="muted">&lt;${esc(n.title)}&gt;</small>` : ''}`;
}

function jqStep(q, n) {
  const start = q.start_npc ? `รับเควสจาก ${jqNpc(q.start_npc)}`
    : (q.prev && q.prev.length ? 'รับต่อทันทีหลังจบเควสก่อนหน้า' : 'ได้รับอัตโนมัติเมื่อผ่านเงื่อนไข');
  return `
    <div class="jq-step${q.shared ? ' shared' : ''}${(q.opens || []).length ? ' final' : ''}">
      <div class="jq-num">${n}</div>
      <div class="jq-body">
        <div class="jq-title">${esc(q.title)}${q.tag ? ` <small class="muted">· ${esc(q.tag)}</small>` : ''}
          ${q.shared ? '<span class="egg-tag">ทำครั้งเดียว ใช้ร่วมทุกฝั่ง</span>' : ''}</div>
        <div class="jq-npc">${start}${q.end_npc ? ` → ส่งเควสที่ ${jqNpc(q.end_npc)}` : ''}</div>
        <div class="jq-req">
          ${q.tamer_level ? `<span class="jq-chip">เทมเมอร์ Lv.${q.tamer_level}+</span>` : ''}
          ${q.digimon_level ? `<span class="jq-chip">ดิจิมอน Lv.${q.digimon_level}+</span>` : ''}
          ${q.need_digimon.map(d => `<span class="jq-chip need">ต้องใช้ ${jqDigi(d)}</span>`).join('')}
          ${(q.need_form || []).map(f => `<span class="jq-chip need">ต้องวิวัฒนาการเป็น ${jqDigi(f)}</span>`).join('')}
          ${(q.need_items || []).map(it => `<span class="jq-chip need">ต้องมี ${jqItem(it, true)}</span>`).join('')}
        </div>
        ${q.objective ? `<div class="jq-obj-text">${esc(q.objective)}</div>` : ''}
        ${q.objectives.length ? `<ul class="jq-objs">${q.objectives.map(o => `<li>${jqObjective(o)}</li>`).join('')}</ul>` : ''}
        ${(q.supply || []).length ? `<div class="jq-rew"><span class="egg-lab">ได้ตอนรับเควส</span><span class="jq-wrap">${q.supply.map(it => jqItem(it)).join('')}</span></div>` : ''}
        ${q.rewards.length ? `<div class="jq-rew"><span class="egg-lab">รางวัล</span><span class="jq-wrap">${q.rewards.map(jqReward).join('')}</span></div>` : ''}
        ${(q.opens || []).length ? `<div class="jq-open">ทำเควสนี้สำเร็จ = ปลดร่าง ${q.opens.map(jqDigi).join(' ')}</div>` : ''}
        ${q.story ? `<details class="jq-story"><summary>อ่านเนื้อเรื่อง</summary><p>${esc(q.story).replace(/\n/g, '<br>')}</p>${q.done_text ? `<p class="muted">${esc(q.done_text).replace(/\n/g, '<br>')}</p>` : ''}</details>` : ''}
      </div>
    </div>`;
}

function renderJogressDetail(slug, sideIdx) {
  const view = document.getElementById('jq-detail');
  const g = (JQ_STATE.items || []).find(x => x.slug === slug);
  document.getElementById('jq-list-view').style.display = 'none';
  view.style.display = '';
  if (!g) { view.innerHTML = '<div class="empty-note">ไม่พบเควสของดิจิมอนนี้ <a href="/jogress">กลับ</a></div>'; return; }
  const si = Math.min(Math.max(parseInt(sideIdx, 10) || 0, 0), g.sides.length - 1);
  const s = g.sides[si];
  view.innerHTML = `
    <div class="patch-nav"><a class="preset-btn" href="/jogress">← รายการเควสโจเกรสทั้งหมด</a>
      <a class="preset-btn" href="${digiHref(g.slug)}"><img src="/images/ui/ui_digimon.png" class="btn-game-icon" alt=""> ไปหน้าดิจิมอน</a></div>
    <div class="panel jq-head">
      <img class="jq-portrait big" src="${esc(g.image || g.icon || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">
      <div>
        <h2>${esc(g.thai_name)} ${g.rank ? `<span class="jq-rank" style="color:${esc(g.rank_color)}">${esc(g.rank)}</span>` : ''}</h2>
        <div class="egg-en">${esc(g.title)}</div>
        <div class="jq-meta"><img src="/images/ui/ui_quest.png" class="stat-icon-inline" alt=""> ${g.quest_count} เควส${g.sides.length > 1 ? ` แยก ${g.sides.length} ฝั่ง (ต้องทำครบทุกฝั่ง)` : ''}</div>
        ${g.reward_items.length ? `<div class="jq-row"><span class="egg-lab">ไอเทมที่ได้จากเควส</span><span class="jq-wrap">${g.reward_items.map(r => jqItem(r)).join('')}</span></div>` : ''}
        ${g.unlock_from_quest.length ? `<div class="jq-meta">กรอบสีทอง = ไอเทมปลดร่าง</div>` : ''}
      </div>
    </div>
    ${g.sides.length > 1 ? `<div class="jq-tabs">${g.sides.map((x, i) => `
      <a class="jq-tab${i === si ? ' active' : ''}" href="${jqHref(g, i)}">
        ${x.partner && x.partner.icon ? `<img src="${esc(x.partner.icon)}" alt="" onerror="this.remove()">` : ''}
        <span>${esc(jqSideName(x))}<small>${x.quest_count} เควส${x.form ? ` · ร่าง ${esc(x.form.name)}` : ''}</small></span></a>`).join('')}</div>` : ''}
    <div class="panel">
      <h3 class="panel-title"><img src="/images/ui/ui_quest.png" class="btn-game-icon" alt=""> ${esc(jqSideName(s))} <span>${s.quest_count} เควส</span></h3>
      <div class="jq-side-sum">
        ${s.partner ? `<div class="jq-row"><span class="egg-lab">ดิจิมอนที่ใช้</span><span class="jq-wrap">${jqDigi(s.partner)}${s.form ? ` → ต้องวิวัฒนาการเป็น ${jqDigi(s.form)}` : ''}</span></div>` : ''}
        ${s.max_tamer_level || s.max_digimon_level ? `<div class="jq-row"><span class="egg-lab">เลเวลที่ต้องใช้</span><span class="jq-wrap">${s.max_tamer_level ? `<span class="jq-chip">เทมเมอร์ Lv.${s.max_tamer_level}</span>` : ''}${s.max_digimon_level ? `<span class="jq-chip">ดิจิมอน Lv.${s.max_digimon_level}</span>` : ''}</span></div>` : ''}
        ${s.reward_items.length ? `<div class="jq-row"><span class="egg-lab">ได้จากฝั่งนี้</span><span class="jq-wrap">${s.reward_items.map(r => jqItem(r)).join('')}</span></div>` : ''}
        ${s.opens.length ? `<div class="jq-row"><span class="egg-lab">ทำครบแล้วปลด</span><span class="jq-wrap">${s.opens.map(jqDigi).join('')}</span></div>` : ''}
      </div>
      <div class="jq-steps">${s.quests.map((q, i) => jqStep(q, i + 1)).join('')}</div>
    </div>`;
  window.scrollTo({ top: 0 });
}

function showJogressList() {
  const lv = document.getElementById('jq-list-view');
  const dv = document.getElementById('jq-detail');
  if (lv) lv.style.display = '';
  if (dv) { dv.style.display = 'none'; dv.innerHTML = ''; }
}


// ==========================================
// 1d. DIGIMON ARCHIVE DECKS (Thai client: dbookdeckdata / dbookcompositiondata)
// ==========================================
const DECK_STATE = { items: null, opt: 'all' };

async function loadDecks() {
  if (!DECK_STATE.items) {
    const el = document.getElementById('deck-opt-pills');
    if (el && !el.innerHTML.trim()) el.innerHTML = SKEL.pills([66, 74, 82, 70, 76]);
    const grid = document.getElementById('deck-grid');
    if (grid) grid.innerHTML = SKEL.decks(6);
    try { DECK_STATE.items = await (await fetch('/api/decks')).json(); } catch (e) { DECK_STATE.items = []; }
    const opts = {};
    DECK_STATE.items.forEach(d => d.effects.forEach(e => { opts[e.option] = opts[e.option] || { ...e, count: 0 }; opts[e.option].count++; }));
    el.innerHTML = `<button class="filter-pill active" data-k="all">ทั้งหมด <small>${DECK_STATE.items.length}</small></button>` +
      Object.values(opts).sort((a, b) => b.count - a.count).map(o =>
        `<button class="filter-pill" data-k="${o.option}">${esc(o.name)} <small>${o.count}</small></button>`).join('');
    el.querySelectorAll('.filter-pill').forEach(b => b.addEventListener('click', () => {
      el.querySelectorAll('.filter-pill').forEach(x => x.classList.toggle('active', x === b));
      DECK_STATE.opt = b.dataset.k;
      renderDecks();
    }));
  }
  renderDecks();
}

function deckMember(m, dup) {
  const inner = `<img src="${esc(m.icon || PLACEHOLDER)}" alt="" onerror="this.src='${PLACEHOLDER}'">
    <span class="deck-m-name">${esc(m.name)}</span>
    ${m.rank ? `<span class="deck-m-rank" style="color:${esc(m.rank_color)}">${esc(m.rank)}</span>` : ''}
    ${dup && m.line ? `<span class="deck-m-line">สาย${esc(m.line)}</span>` : ''}`;
  return m.slug ? `<a class="deck-m" href="${digiHref(m.slug)}" title="${esc(m.title)}">${inner}</a>` : `<span class="deck-m">${inner}</span>`;
}

function deckEffect(e) {
  const ic = e.icon && e.icon.includes('/') ? `<img src="${esc(e.icon)}" class="stat-icon-inline" alt="">` : (e.icon || '');
  return `<div class="deck-eff${e.always ? '' : ' proc'}"><span class="deck-eff-ic">${ic}</span>
    <div><b>${esc(e.name)}${e.option === 4 ? '' : ` +${e.value}%`}</b>
      <div class="deck-eff-when">${e.always ? 'ตลอดเวลา' : `${esc(e.on)} · มีโอกาส ${e.chance}%${e.seconds ? ` · นาน ${e.seconds} วินาที` : ''}`}</div></div></div>`;
}

function renderDecks() {
  const grid = document.getElementById('deck-grid');
  if (!grid || !DECK_STATE.items) return;
  const q = (document.getElementById('deck-search-input').value || '').trim().toLowerCase();
  const items = DECK_STATE.items.filter(d =>
    (DECK_STATE.opt === 'all' || d.effects.some(e => String(e.option) === DECK_STATE.opt)) &&
    (!q || JSON.stringify([d.name, d.desc, d.members.map(m => [m.name, m.title, m.line]), d.effects.map(e => e.name)]).toLowerCase().includes(q)));
  document.getElementById('deck-count').textContent = items.length;
  if (!items.length) { grid.innerHTML = '<div class="empty-note">ไม่พบเด็คที่ตรงกับคำค้น</div>'; return; }
  const want = DECK_STATE.focus;
  if (want && !DECK_STATE.items.some(d => String(d.id) === want || d.name === want)) {
    showNotFoundPage('decks/' + want, `ไม่พบข้อมูลเด็ค "${want}" ในระบบ`);
    return;
  }
  grid.innerHTML = items.map(d => {
    const isFocus = want && (String(d.id) === want || d.name === want);
    return `
    <div class="deck-card${isFocus ? ' focus' : ''}" id="deck-${d.id}">
      <div class="deck-head"><h3>${esc(d.name)}</h3><span class="deck-count">${d.members.length} ตัว</span></div>
      ${d.desc ? `<details class="deck-desc"><summary>เรื่องราวของเด็ค</summary><p>${esc(d.desc)}</p></details>` : ''}
      <div class="deck-sub">ดิจิมอนที่ต้องสะสม (เปิดร่างนี้ในสารานุกรมให้ครบ)</div>
      <div class="deck-members">${d.members.map(m => deckMember(m)).join('')}</div>
      <div class="deck-sub">บัฟเมื่อสะสมครบเด็ค</div>
      <div class="deck-effs">${d.effects.map(deckEffect).join('')}</div>
    </div>`;
  }).join('');
  if (want) {
    const matched = items.find(d => String(d.id) === want || d.name === want);
    const el = matched ? document.getElementById('deck-' + matched.id) : null;
    if (el) setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  }
}


// pill-wheel-scroll: the mouse wheel scrolls horizontal filter rows sideways
document.addEventListener('wheel', ev => {
  const row = ev.target.closest && ev.target.closest('.filter-pills-row');
  if (!row || row.scrollWidth <= row.clientWidth || Math.abs(ev.deltaY) <= Math.abs(ev.deltaX)) return;
  const max = row.scrollWidth - row.clientWidth;
  if ((ev.deltaY < 0 && row.scrollLeft <= 0) || (ev.deltaY > 0 && row.scrollLeft >= max - 1)) return;
  row.scrollLeft += ev.deltaY;
  ev.preventDefault();
}, { passive: false });


function showDungeonList() {
  const lv = document.getElementById('dg-list-view'), dv = document.getElementById('dg-detail-view');
  if (lv) lv.style.display = '';
  if (dv) { dv.style.display = 'none'; dv.innerHTML = ''; }
  if (!(STATE.dungeons.items || []).length) loadDungeons();
}

async function openDungeonPage(ref) {
  const lv = document.getElementById('dg-list-view'), dv = document.getElementById('dg-detail-view');
  lv.style.display = 'none';
  dv.style.display = '';
  dv.innerHTML = SKEL.dungeonDetail();
  if (!(STATE.dungeons.items || []).length) await loadDungeons();
  const d = STATE.dungeons.items.find(x => x.slug === ref || x.key === ref || x.name === ref);
  if (!d) {
    dv.innerHTML = `<div class="empty-note">
      <div style="font-size:1.1rem;font-weight:700;color:var(--color-danger)">ไม่พบดันเจี้ยน "${esc(ref)}" ในระบบ</div>
      <p class="muted" style="margin:8px 0 14px">ลิงก์อาจถูกพิมพ์ไม่ถูกต้อง หรือไม่มีดันเจี้ยนชื่อนี้</p>
      <a class="preset-btn" href="/dungeons">← กลับหน้ารวมดันเจี้ยน</a>
    </div>`;
    return;
  }
  if (d.slug && ref !== d.slug) {
    try { window.history.replaceState(null, '', '/dungeon/' + encodeURIComponent(d.slug)); } catch (e) { }
  }
  const boss = d.monsters.find(m => m.boss) || d.monsters[d.monsters.length - 1];
  const npc0 = d.entry_npcs[0];
  document.title = `${d.name} - DMO Thai Wiki`;
  dv.innerHTML = `
    <div class="patch-nav"><a class="preset-btn" href="/dungeons">← ดันเจี้ยนทั้งหมด</a></div>
    <div class="panel dg-page-head">
      <div class="dg-boss big">${boss && boss.icon ? `<img src="${esc(boss.icon)}" alt="" onerror="this.remove()">` : ''}</div>
      <div>
        <h2>${esc(d.name)}${d.variant ? ` <span class="jq-chip">${esc(d.variant)}</span>` : ''}</h2>
        <div class="dg-meta">${d.instance ? 'อินสแตนซ์' : 'แมพดันเจี้ยน (เดินเข้าได้)'}${d.map ? ` · แมพ ${esc(d.map)}` : ''}${d.players ? ` · สูงสุด ${d.players} คน` : ''}
          ${d.level_range.length ? ` · มอน Lv.${d.level_range[0]}${d.level_range[1] !== d.level_range[0] ? '-' + d.level_range[1] : ''}` : ''}</div>
        ${boss ? `<div class="dg-meta">บอส <b>${esc(boss.name)}</b> · Lv.${boss.level} · HP <b class="dg-hp">${fmtNum(boss.hp)}</b></div>` : ''}
        ${npc0 ? `<div class="dg-meta">เข้าที่ ${esc(npc0.name)} · ${esc(npc0.map || 'NPC กิจกรรม')}</div>` : ''}
      </div>
    </div>
    ${dgDetail(d)}`;
  window.scrollTo({ top: 0 });
}


// ---- NPC exchange lists: loaded when opened, searchable, grouped by item, paged ----------------------
const EXCH_CACHE = {};
const EXCH_PAGE = 15;   // groups per page

function exchBlock(n) {
  const id = `ex-${n.id}-${Math.random().toString(36).slice(2, 7)}`;
  return `<details class="dg-exch" ontoggle="if(this.open) openExchange(${n.id}, '${id}')">
    <summary>${dgNpc(n)} <span class="muted">· ${n.total} รายการ</span></summary>
    <div class="dg-exch-box" id="${id}" data-ids="${(n.trade_ids || []).join(',')}">
      ${SKEL.exchange(4)}</div></details>`;
}

async function openExchange(npcId, boxId) {
  const box = document.getElementById(boxId);
  if (!box || box.dataset.ready) return;
  if (!EXCH_CACHE[npcId]) {
    try { EXCH_CACHE[npcId] = await (await fetch(`/api/npc-exchange/${npcId}`)).json(); } catch (e) { EXCH_CACHE[npcId] = []; }
  }
  const ids = box.dataset.ids ? box.dataset.ids.split(',').map(Number) : null;
  box._trades = ids ? ids.map(i => EXCH_CACHE[npcId][i]).filter(Boolean) : EXCH_CACHE[npcId];
  box.dataset.ready = '1';
  box.dataset.page = '0';
  box.innerHTML = `
    <div class="dg-exch-tools">
      <input type="text" class="dg-exch-search" placeholder="ค้นหาในรายการแลก (${box._trades.length} รายการ)..." oninput="this.closest('.dg-exch-box').dataset.page='0'; renderExchange('${boxId}')">
      <button class="preset-btn" onclick="toggleExchangeGroups('${boxId}', true)">เปิดทุกกลุ่ม</button>
      <button class="preset-btn" onclick="toggleExchangeGroups('${boxId}', false)">ปิดทุกกลุ่ม</button>
    </div>
    <div class="dg-exch-list"></div>
    <div class="dg-exch-pages"></div>`;
  renderExchange(boxId);
}

function exchGroupKey(name) {
  // "กล่องแอดเวนเจอร์ที่สมบูรณ์ Lv 12 [HT/EV]" -> "กล่องแอดเวนเจอร์ที่สมบูรณ์ [HT/EV]"
  return name.replace(/\s*Lv\.?\s*\d+/i, '').replace(/\s+/g, ' ').trim();
}

function exchRow(t) {
  return `<div class="dg-trade">${dgItem(t.item)}<span class="dg-arrow">⇐</span><span class="jq-wrap">${t.mats.map(m => dgItem(m, true)).join('')}</span>${t.rate < 100 ? `<span class="muted">โอกาส ${t.rate}%</span>` : ''}${t.cost ? fmtMoney(t.cost) : ''}</div>`;
}

function renderExchange(boxId) {
  const box = document.getElementById(boxId);
  if (!box || !box._trades) return;
  const q = (box.querySelector('.dg-exch-search').value || '').trim().toLowerCase();
  const list = box._trades.filter(t => !q || [t.item.name, ...t.mats.map(m => m.name)].join(' ').toLowerCase().includes(q));
  const groups = [];
  const byKey = {};
  list.forEach(t => {
    const k = exchGroupKey(t.item.name);
    if (!byKey[k]) { byKey[k] = { key: k, icon: t.item.icon, items: [] }; groups.push(byKey[k]); }
    byKey[k].items.push(t);
  });
  const pages = Math.max(1, Math.ceil(groups.length / EXCH_PAGE));
  const page = Math.min(Number(box.dataset.page || 0), pages - 1);
  const shown = groups.slice(page * EXCH_PAGE, (page + 1) * EXCH_PAGE);
  box.querySelector('.dg-exch-list').innerHTML = !list.length ? '<div class="muted">ไม่พบรายการที่ค้นหา</div>' :
    shown.map(g => g.items.length === 1 ? exchRow(g.items[0]) : `
      <details class="dg-exch-group"${q ? ' open' : ''}>
        <summary>${g.icon ? `<img src="${esc(g.icon)}" alt="" onerror="this.remove()">` : ''}<b>${esc(g.key)}</b>
          <span class="muted">${g.items.length} ระดับ</span></summary>
        <div class="dg-trades">${g.items.map(exchRow).join('')}</div>
      </details>`).join('');
  box.querySelector('.dg-exch-pages').innerHTML = pages < 2 ? `<span class="muted">${list.length} รายการ · ${groups.length} กลุ่ม</span>` :
    `<span class="muted">${list.length} รายการ · ${groups.length} กลุ่ม · หน้า</span>` +
    Array.from({ length: pages }, (_, i) => `<button class="dg-page-btn${i === page ? ' active' : ''}" onclick="gotoExchangePage('${boxId}', ${i})">${i + 1}</button>`).join('');
}

function gotoExchangePage(boxId, p) {
  const box = document.getElementById(boxId);
  box.dataset.page = String(p);
  renderExchange(boxId);
  box.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function toggleExchangeGroups(boxId, open) {
  document.querySelectorAll(`#${boxId} .dg-exch-group`).forEach(d => { d.open = open; });
}

// ==========================================
// 2. TAMERS (เทมเมอร์ในเซิร์ฟเวอร์ไทย)
// ==========================================
const TAMER_DETAIL_CACHE = {};
let ACTIVE_TM_VIEWER = null;

function disposeTamerModelViewer() {
  if (!ACTIVE_TM_VIEWER) return;
  try {
    if (ACTIVE_TM_VIEWER.raf) cancelAnimationFrame(ACTIVE_TM_VIEWER.raf);
    if (ACTIVE_TM_VIEWER.onResize) window.removeEventListener('resize', ACTIVE_TM_VIEWER.onResize);
    if (ACTIVE_TM_VIEWER.controls) ACTIVE_TM_VIEWER.controls.dispose();
    if (ACTIVE_TM_VIEWER.envRT) ACTIVE_TM_VIEWER.envRT.dispose();
    if (ACTIVE_TM_VIEWER.renderer) {
      ACTIVE_TM_VIEWER.renderer.dispose();
      ACTIVE_TM_VIEWER.renderer.domElement?.remove();
    }
  } catch (e) { }
  ACTIVE_TM_VIEWER = null;
}

function toggleTamerModelRotate() {
  if (!ACTIVE_TM_VIEWER) return;
  ACTIVE_TM_VIEWER.controls.autoRotate = !ACTIVE_TM_VIEWER.controls.autoRotate;
  const btn = document.getElementById('tm-btn-rot');
  if (btn) btn.classList.toggle('active', ACTIVE_TM_VIEWER.controls.autoRotate);
}

function toggleTamerModelWireframe() {
  if (!ACTIVE_TM_VIEWER || !ACTIVE_TM_VIEWER.model) return;
  ACTIVE_TM_VIEWER.wireframe = !ACTIVE_TM_VIEWER.wireframe;
  ACTIVE_TM_VIEWER.model.traverse(obj => {
    if (obj.isMesh && obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      mats.forEach(m => { m.wireframe = ACTIVE_TM_VIEWER.wireframe; });
    }
  });
  const btn = document.getElementById('tm-btn-wire');
  if (btn) btn.classList.toggle('active', ACTIVE_TM_VIEWER.wireframe);
}

function resetTamerModelCamera() {
  if (!ACTIVE_TM_VIEWER) return;
  const { camera, controls, homeCamPos, homeTarget } = ACTIVE_TM_VIEWER;
  camera.position.copy(homeCamPos);
  controls.target.copy(homeTarget);
  controls.update();
}

function _createStudioStageRig(stage, opts = {}) {
  const width = stage.clientWidth || opts.defaultW || 640;
  const height = stage.clientHeight || opts.defaultH || 460;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(opts.fov || 34, width / height, 0.5, 5000);
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'default',
  });
  const pr = Math.min(Math.max(window.devicePixelRatio || 1, 1.35), 1.65);
  renderer.setPixelRatio(pr);
  renderer.setSize(width, height);
  renderer.outputEncoding = THREE.sRGBEncoding;
  if (THREE.ACESFilmicToneMapping !== undefined) {
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = opts.exposure || 1.06;
  }
  stage.insertBefore(renderer.domElement, stage.firstChild);

  scene.add(new THREE.HemisphereLight(0xf8fafc, 0x1e293b, 0.80));

  const key = new THREE.DirectionalLight(0xfffaf0, 1.18);
  key.position.set(130, 250, 240);
  scene.add(key);

  const fill = new THREE.DirectionalLight(0xe0f2fe, 0.52);
  fill.position.set(-130, 120, 220);
  scene.add(fill);

  const rim = new THREE.DirectionalLight(opts.rimColor || 0xa78bfa, 0.85);
  rim.position.set(-160, 175, -185);
  scene.add(rim);

  return { width, height, scene, camera, renderer, envRT: null, shadowFloor: null };
}

function _enhanceStudioGLTFModel(root, renderer) {
  if (!root) return;
  const maxAniso = Math.min(8, renderer?.capabilities?.getMaxAnisotropy?.() || 4);
  root.traverse(obj => {
    if (!obj.isMesh || !obj.material) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    mats.forEach(m => {
      m.side = THREE.DoubleSide;
      if (m.name && m.name.startsWith('add_')) {
        m.blending = THREE.AdditiveBlending;
        m.depthWrite = false;
        m.transparent = true;
      } else if (typeof m.roughness === 'number') {
        m.roughness = Math.min(m.roughness, 0.68);
      }
      ['map', 'emissiveMap'].forEach(k => {
        const tex = m[k];
        if (tex) {
          tex.anisotropy = maxAniso;
          tex.minFilter = THREE.LinearMipmapLinearFilter;
          tex.magFilter = THREE.LinearFilter;
          tex.needsUpdate = true;
        }
      });
    });
  });
}

function _buildMagicHaloGroup(radius, colorHex, withDots = true) {
  const g = new THREE.Group();
  const rInner = new THREE.Mesh(
    new THREE.RingGeometry(radius * 0.86, radius * 0.94, 72),
    new THREE.MeshBasicMaterial({ color: colorHex, side: THREE.DoubleSide, transparent: true, opacity: 0.78 })
  );
  rInner.rotation.x = -Math.PI / 2;
  g.add(rInner);

  const rOuter = new THREE.Mesh(
    new THREE.RingGeometry(radius * 1.06, radius * 1.11, 72),
    new THREE.MeshBasicMaterial({ color: colorHex, side: THREE.DoubleSide, transparent: true, opacity: 0.34 })
  );
  rOuter.rotation.x = -Math.PI / 2;
  g.add(rOuter);

  if (withDots) {
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      pts.push(Math.cos(a) * radius * 1.20, 0.4, Math.sin(a) * radius * 1.20);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    const dots = new THREE.Points(
      geo,
      new THREE.PointsMaterial({ color: 0xe9d5ff, size: Math.max(radius * 0.14, 1.4), transparent: true, opacity: 0.85 })
    );
    g.add(dots);
  }
  return g;
}

function initTamerModelViewer(tid, modelUrl, meta) {
  disposeTamerModelViewer();
  const host = document.getElementById(`tm-model-viewer-${tid}`);
  if (!host) return;
  if (!modelUrl) {
    host.innerHTML = '<div class="empty-note">ไม่พบไฟล์โมเดล 3D สำหรับเทมเมอร์ตัวนี้</div>';
    return;
  }

  host.innerHTML = `
    <div class="tm-model-toolbar">
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button id="tm-btn-rot" class="filter-pill active" type="button" onclick="toggleTamerModelRotate()">หมุนอัตโนมัติ</button>
        <button id="tm-btn-wire" class="filter-pill" type="button" onclick="toggleTamerModelWireframe()">Wireframe</button>
        <button class="filter-pill" type="button" onclick="resetTamerModelCamera()">รีเซ็ตมุมมอง</button>
      </div>
      <a class="filter-pill" href="${esc(modelUrl)}" download style="text-decoration:none">ดาวน์โหลด .glb</a>
    </div>
    <div id="tm-stage-${tid}" class="tm-model-stage">
      <div id="tm-status-${tid}" class="tm-model-status">กำลังโหลดโมเดล 3D...</div>
      <div class="tm-model-hint">ลากเพื่อหมุน 360° · เลื่อนเมาส์เพื่อซูม · คลิกขวาเพื่อเลื่อน</div>
    </div>`;

  const stage = document.getElementById(`tm-stage-${tid}`);
  const statusEl = document.getElementById(`tm-status-${tid}`);
  if (!stage || typeof THREE === 'undefined' || !THREE.GLTFLoader) {
    if (statusEl) statusEl.textContent = 'ไม่สามารถเริ่มตัวแสดงผล 3D ได้';
    return;
  }

  const { scene, camera, renderer, envRT } = _createStudioStageRig(stage, {
    defaultW: 460,
    defaultH: 460,
    fov: 36,
    rimColor: 0x7dd3fc,
    shadowRadius: 150,
  });

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 1.6;

  const state = {
    renderer,
    envRT,
    controls,
    camera,
    scene,
    model: null,
    wireframe: false,
    homeCamPos: new THREE.Vector3(0, 100, 260),
    homeTarget: new THREE.Vector3(0, 75, 0),
    raf: 0,
    onResize: null
  };
  ACTIVE_TM_VIEWER = state;

  state.onResize = () => {
    if (!stage.isConnected) return;
    const w = stage.clientWidth || 460;
    const h = stage.clientHeight || 460;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener('resize', state.onResize);

  const loader = new THREE.GLTFLoader();
  loader.load(
    modelUrl,
    gltf => {
      if (ACTIVE_TM_VIEWER !== state) return;
      const root = gltf.scene;
      _enhanceStudioGLTFModel(root, renderer);
      scene.add(root);
      state.model = root;

      const box = new THREE.Box3().setFromObject(root);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z, 1);

      const halo = _buildMagicHaloGroup(maxDim * 0.25, 0x38bdf8, false);
      halo.position.set(center.x, box.min.y + 0.4, center.z);
      scene.add(halo);

      const fovRad = (camera.fov * Math.PI) / 180;
      const dist = (maxDim / 2) / Math.tan(fovRad / 2) * 1.45;
      state.homeTarget.copy(center);
      state.homeCamPos.set(center.x + dist * 0.18, center.y + size.y * 0.08, center.z + dist);
      resetTamerModelCamera();
      if (statusEl) statusEl.remove();
    },
    undefined,
    () => {
      if (statusEl) statusEl.textContent = 'โหลดโมเดล 3D ไม่สำเร็จ';
    }
  );

  const animate = () => {
    if (ACTIVE_TM_VIEWER !== state) return;
    state.raf = requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  };
  animate();
}

function renderSatsumaSkillPanel() {
  const host = document.getElementById('tm-satsuma-panel');
  if (!host) return;
  const sys = STATE.tamers.skillSystem;
  if (!sys || (!sys.satsuma && !(sys.active_skills || []).length)) {
    host.innerHTML = '';
    return;
  }
  const sat = sys.satsuma || {};
  const gek = sys.gekomon || {};
  const baseP = sys.base_passive || {};
  const actList = sys.active_skills || [];
  const pasList = sys.passive_skills || [];
  const cleanTitle = (sys.title || 'เทมเมอร์ทุกตัวใช้สกิลไหนก็ได้ (รับจากซาสึมะ)').replace(/^ปรับปรุงระบบเซิร์ฟไทย:\s*/, '');

  host.innerHTML = `
    <div class="tm-satsuma-banner">
      <div class="tm-satsuma-head">
        <div class="tm-satsuma-title-wrap">
          <span style="font-size:1.05rem;font-weight:800;color:var(--text-main)">${esc(cleanTitle)}</span>
        </div>
        ${baseP.name ? `
          <span class="tm-box-chip" title="${esc(baseP.desc || '')}">
            ${baseP.icon ? `<img src="${esc(baseP.icon)}" alt="" onerror="this.remove()">` : ''}
            <span>ติดตัวทุกตัว: <strong>${esc(baseP.name)}</strong></span>
          </span>` : ''}
      </div>
      <div style="font-size:0.84rem;color:var(--text-sub);margin-top:6px;line-height:1.55">${esc(sys.summary || '')}</div>

      <div class="tm-satsuma-npc-row">
        <div class="tm-npc-card">
          ${sat.image ? `<img class="tm-npc-portrait" src="${esc(sat.image)}" alt="${esc(sat.name)}" onerror="this.remove()">` : ''}
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
              <strong>${esc(sat.name || 'NPC ซาสึมะ')}</strong>
              <span class="tm-tag starter">${esc(sat.quest || 'เลือกสกิลเทมเมอร์!')}</span>
            </div>
            <div class="muted" style="font-size:0.76rem;margin-top:2px">${esc(sat.role || '')}</div>
            <div class="tm-box-list">
              ${(sat.rewards || []).map(r => `
                <span class="tm-box-chip">
                  ${r.icon ? `<img src="${esc(r.icon)}" alt="" onerror="this.remove()">` : ''}
                  <span>${esc(r.name)} <strong>×${r.qty}</strong></span>
                </span>`).join('')}
            </div>
          </div>
        </div>

        <div class="tm-npc-card">
          ${gek.image ? `<img class="tm-npc-portrait" src="${esc(gek.image)}" alt="${esc(gek.name)}" onerror="this.remove()">` : ''}
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
              <strong>${esc(gek.name || 'NPC เกโคมอน')}</strong>
              <span class="tm-tag unlock">ร้านแลกเปลี่ยนเพิ่มเติม</span>
            </div>
            <div class="muted" style="font-size:0.76rem;margin-top:2px">${esc(gek.role || '')}</div>
            <div class="tm-box-list">
              ${(gek.shop || []).map(r => `
                <span class="tm-box-chip">
                  ${r.icon ? `<img src="${esc(r.icon)}" alt="" onerror="this.remove()">` : ''}
                  <span>${esc(r.name.replace(' [กิจกรรม]', ''))} <strong style="color:#fbbf24">(${esc(r.cost)})</strong></span>
                </span>`).join('')}
            </div>
          </div>
        </div>
      </div>

      <details class="tm-revamp-details">
        <summary class="tm-revamp-summary">
          <span>ดูคลังสกิลเทมเมอร์ที่เลือกใส่ได้ทุกตัว (แอคทีฟ ${actList.length} สกิล · พาสซีฟ ${pasList.length} สกิล) — กดเพื่อเปิด/ซ่อน</span>
          <span class="tm-tag thai">สูงสุด 1 แอคทีฟ + 2 พาสซีฟ</span>
        </summary>
        <div style="margin-top:10px;font-size:0.8rem;font-weight:700;color:#7dd3fc"><img src="/images/Fire.png" class="stat-icon-inline" alt=""> สกิลแอคทีฟเฉพาะ (${actList.length} สกิล — เลือกใส่ได้สูงสุด 1 ชนิด)</div>
        <div class="tm-revamp-grid">
          ${actList.map(s => `
            <div class="tm-revamp-skill">
              <div class="tm-skill-ic">${s.icon ? `<img src="${esc(s.icon)}" alt="" onerror="this.remove()">` : ''}</div>
              <div style="min-width:0;flex:1">
                <div style="font-weight:700">${esc(s.name)}</div>
                ${s.former_tamer ? `<div style="font-size:0.71rem;color:#94a3b8">เดิม: ${esc(s.former_tamer)}</div>` : ''}
                <div style="font-size:0.75rem;color:var(--text-muted);margin-top:3px;line-height:1.4">${esc(s.desc)}</div>
              </div>
            </div>`).join('')}
        </div>
        <div style="margin-top:12px;font-size:0.8rem;font-weight:700;color:#a78bfa"><img src="/images/DE.png" class="stat-icon-inline" alt=""> สกิลพาสซีฟเฉพาะ (${pasList.length} สกิล — เลือกใส่ได้สูงสุด 2 ชนิด)</div>
        <div class="tm-revamp-grid">
          ${pasList.map(s => `
            <div class="tm-revamp-skill">
              <div class="tm-skill-ic">${s.icon ? `<img src="${esc(s.icon)}" alt="" onerror="this.remove()">` : ''}</div>
              <div style="min-width:0;flex:1">
                <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap">
                  <strong>${esc(s.name)}</strong>
                  <span class="tm-tag">${esc(s.attr)}</span>
                </div>
                <div style="font-size:0.75rem;color:var(--text-muted);margin-top:3px;line-height:1.4">${esc(s.desc)}</div>
              </div>
            </div>`).join('')}
        </div>
      </details>
    </div>`;
}

async function loadTamers() {
  const grid = document.getElementById('tamer-grid');
  if (STATE.tamers.items.length) {
    renderSatsumaSkillPanel();
    renderTamers();
    return;
  }
  if (grid && !grid.dataset.loaded) {
    grid.innerHTML = SKEL.tamers(8);
  }
  try {
    const res = await fetch('/api/tamers');
    const data = await res.json();
    STATE.tamers.items = data.items || [];
    STATE.tamers.skillSystem = data.skill_system || null;
    STATE.tamers.statusData = data.tamer_status || null;
    if (TM_STATUS_STATE.pendingRender) {
      TM_STATUS_STATE.pendingRender = false;
      renderTamerStatusView();
    }
    renderSatsumaSkillPanel();
    const seriesRow = document.getElementById('tm-series-pills');
    if (seriesRow) {
      const seriesList = data.series || [];
      seriesRow.innerHTML =
        `<button class="filter-pill ${STATE.tamers.series === 'all' ? 'active' : ''}" onclick="setTamerSeriesFilter('all', this)">ทั้งหมด (${STATE.tamers.items.length})</button>` +
        seriesList.map(s => {
          const cnt = STATE.tamers.items.filter(x => x.series === s).length;
          return `<button class="filter-pill ${STATE.tamers.series === s ? 'active' : ''}" onclick="setTamerSeriesFilter('${esc(s)}', this)">${esc(s)} (${cnt})</button>`;
        }).join('');
    }
    if (grid) grid.dataset.loaded = '1';
    renderTamers();
  } catch (e) {
    if (grid) grid.innerHTML = '<div class="empty-note">ไม่สามารถโหลดข้อมูลเทมเมอร์ได้</div>';
  }
}

function setTamerSeriesFilter(series, btn) {
  STATE.tamers.series = series;
  document.querySelectorAll('#tm-series-pills .filter-pill').forEach(b => b.classList.toggle('active', b === btn));
  renderTamers();
}

function setTamerTypeFilter(kind, btn) {
  STATE.tamers.type = kind;
  document.querySelectorAll('#tm-type-pills .filter-pill').forEach(b => b.classList.toggle('active', b === btn));
  renderTamers();
}

function renderTamers() {
  const grid = document.getElementById('tamer-grid');
  const countEl = document.getElementById('tamer-count-display');
  if (!grid) return;
  const q = (document.getElementById('tamer-search-input')?.value || '').trim().toLowerCase();
  const filtered = (STATE.tamers.items || []).filter(t => {
    if (STATE.tamers.series !== 'all' && t.series !== STATE.tamers.series) return false;
    if (STATE.tamers.type === 'starter' && !t.starter) return false;
    if (STATE.tamers.type === 'unlock' && t.starter) return false;
    if (STATE.tamers.type === 'male' && t.gender !== 'ชาย') return false;
    if (STATE.tamers.type === 'female' && t.gender !== 'หญิง') return false;
    if (!q) return true;
    const hay = [
      t.name_th, t.name_en, t.short_th, t.series, t.series_en, t.partner,
      ...(t.active_skills || []).map(s => s.name),
      ...(t.passive_skills || []).map(s => s.name),
    ].join(' ').toLowerCase();
    return hay.includes(q);
  });
  if (countEl) countEl.textContent = String(filtered.length);
  if (!filtered.length) {
    grid.innerHTML = '<div class="empty-note">ไม่พบเทมเมอร์ที่ตรงกับเงื่อนไข</div>';
    return;
  }
  grid.innerHTML = filtered.map(t => {
    const st = t.stats_lv180 || {};
    const sys = STATE.tamers.skillSystem;
    const satIcon = sys?.satsuma?.rewards?.[0]?.icon || '';
    const legacyAct = (t.active_skills || [])[0];
    const hasUlt = (t.extra_skill_tiers || []).length > 0;
    const skillChips = [
      `<span class="tm-skill-chip active">${satIcon ? `<img src="${esc(satIcon)}" alt="" onerror="this.remove()">` : ''}ซาสึมะ: เลือกใส่ได้ 16+8 สกิล</span>`,
      legacyAct ? `<span class="tm-skill-chip" title="สกิลเฉพาะดั้งเดิม">${legacyAct.icon ? `<img src="${esc(legacyAct.icon)}" alt="" onerror="this.remove()">` : ''}เดิม: ${esc(legacyAct.name)}</span>` : '',
      hasUlt ? `<span class="tm-skill-chip passive">มีขั้นสุดยอด</span>` : ''
    ].filter(Boolean).join('');
    return `
      <a class="tamer-card" href="/tamer/${encodeURIComponent(t.slug || t.name_th || t.id)}">
        <div class="tm-card-top">
          <span class="tm-tag ${t.starter ? 'starter' : 'unlock'}">${t.starter ? 'เริ่มต้นฟรี' : 'ปลดล็อก / แพ็คเกจ'}</span>
          <span class="tm-tag">${esc(t.gender || '-')}</span>
          ${t.in_thai ? `<span class="tm-tag thai">TH เซิร์ฟไทย</span>` : ''}
        </div>
        <div class="tm-body-row">
          <div class="tm-avatar-wrap">
            <img src="${esc(t.portrait_lg || t.portrait_sm || PLACEHOLDER)}" alt="${esc(t.name_th)}" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
          </div>
          <div class="tm-head-info">
            <div class="tm-name-th">${esc(t.name_th)}</div>
            <div class="tm-name-en">${esc(t.name_en)}</div>
            <div class="tm-meta-row">
              <span>${esc(t.series)}</span>
              ${t.partner ? `<span>· คู่หู ${esc(t.partner)}</span>` : ''}
            </div>
            <div class="tm-meta-row"><span>${esc(t.role)}</span></div>
          </div>
        </div>
        ${t.bio ? `<div class="tm-bio-clip">${esc(t.bio)}</div>` : ''}
        <div class="tm-skill-pills">${skillChips}</div>
        <div class="tm-stats-mini" title="สเตตัสพื้นฐาน Lv.180">
          <div><span>HP</span><strong>${fmtNum(st.hp || 0)}</strong></div>
          <div><span>DS</span><strong>${fmtNum(st.ds || 0)}</strong></div>
          <div><span>MS</span><strong>${fmtNum(st.ms || 0)}</strong></div>
          <div><span>AT</span><strong>${fmtNum(st.at || 0)}</strong></div>
          <div><span>DE</span><strong>${fmtNum(st.de || 0)}</strong></div>
        </div>
      </a>`;
  }).join('');
}

function showTamerView(view) {
  const isStatus = view === 'status';
  const swList = document.getElementById('tm-sw-list');
  const swStatus = document.getElementById('tm-sw-status');
  if (swList) swList.classList.toggle('active', !isStatus);
  if (swStatus) swStatus.classList.toggle('active', isStatus);
  const lv = document.getElementById('tm-list-view');
  const dv = document.getElementById('tm-detail-view');
  const sv = document.getElementById('tm-status-view');
  if (isStatus) {
    disposeTamerModelViewer();
    if (lv) lv.style.display = 'none';
    if (dv) { dv.style.display = 'none'; dv.innerHTML = ''; }
    if (sv) sv.style.display = '';
    openTamerStatusView();
  } else {
    if (sv) sv.style.display = 'none';
    showTamerList();
  }
}

function showTamerList() {
  disposeTamerModelViewer();
  const swList = document.getElementById('tm-sw-list');
  const swStatus = document.getElementById('tm-sw-status');
  if (swList) swList.classList.add('active');
  if (swStatus) swStatus.classList.remove('active');
  const lv = document.getElementById('tm-list-view');
  const dv = document.getElementById('tm-detail-view');
  const sv = document.getElementById('tm-status-view');
  if (lv) lv.style.display = '';
  if (dv) { dv.style.display = 'none'; dv.innerHTML = ''; }
  if (sv) sv.style.display = 'none';
  loadTamers();
}

function tmSkillCard(s, badgeLabel, badgeCls) {
  return `
    <div class="tm-skill-card">
      <div class="tm-skill-ic">${s.icon ? `<img src="${esc(s.icon)}" alt="" onerror="this.remove()">` : ''}</div>
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <strong>${esc(s.name)}</strong>
          <span class="tm-tag ${badgeCls}">${esc(badgeLabel)}</span>
        </div>
        <div style="font-size:0.82rem;color:var(--text-muted);margin-top:4px;line-height:1.45">${esc(s.desc || '-')}</div>
      </div>
    </div>`;
}

function updateTamerStatLv(tid, lvRaw) {
  const t = TAMER_DETAIL_CACHE[tid];
  if (!t || !t.stats_levels || !t.stats_levels.length) return;
  const maxLv = t.stats_levels.length;
  const lv = Math.max(1, Math.min(maxLv, Number(lvRaw) || 1));
  const row = t.stats_levels[lv - 1];
  const badge = document.getElementById('tm-lv-badge');
  if (badge) badge.textContent = `Lv.${lv}`;
  const slider = document.getElementById('tm-lv-slider');
  if (slider) slider.value = String(lv);
  const vals = ['hp', 'ds', 'ms', 'de', 'at'];
  vals.forEach((k, idx) => {
    const el = document.getElementById(`tm-stat-${k}`);
    if (el) el.textContent = fmtNum(row[idx]);
  });
}

async function openTamerPage(ref) {
  disposeTamerModelViewer();
  const swList = document.getElementById('tm-sw-list');
  const swStatus = document.getElementById('tm-sw-status');
  if (swList) swList.classList.add('active');
  if (swStatus) swStatus.classList.remove('active');
  const lv = document.getElementById('tm-list-view');
  const dv = document.getElementById('tm-detail-view');
  const sv = document.getElementById('tm-status-view');
  if (!lv || !dv) return;
  lv.style.display = 'none';
  if (sv) sv.style.display = 'none';
  dv.style.display = '';
  dv.innerHTML = SKEL.tamerDetail();

  const refStr = String(ref || '').trim();
  let t = TAMER_DETAIL_CACHE[refStr] || null;
  if (!t || !STATE.tamers.skillSystem) {
    try {
      const res = await fetch(`/api/tamers/${encodeURIComponent(refStr)}`);
      if (res.ok) {
        const data = await res.json();
        t = data.tamer;
        if (t) {
          TAMER_DETAIL_CACHE[t.id] = t;
          if (t.slug) TAMER_DETAIL_CACHE[t.slug] = t;
        }
        if (data.skill_system) STATE.tamers.skillSystem = data.skill_system;
      }
    } catch (e) { }
  }
  if (!t) {
    dv.innerHTML = `<div class="empty-note">
      <div style="font-size:1.1rem;font-weight:700;color:var(--color-danger)">ไม่พบข้อมูลเทมเมอร์ "${esc(refStr)}" ในระบบ</div>
      <p class="muted" style="margin:8px 0 14px">ลิงก์อาจถูกพิมพ์ไม่ถูกต้อง หรือไม่มีเทมเมอร์ชื่อนี้</p>
      <a class="preset-btn" href="/tamers">← กลับหน้ารวมเทมเมอร์</a>
    </div>`;
    return;
  }
  if (t.slug && refStr !== t.slug) {
    try { window.history.replaceState(null, '', '/tamer/' + encodeURIComponent(t.slug)); } catch (e) { }
  }

  document.title = `${t.name_th} (${t.name_en}) - DMO Thai Wiki`;
  const initLv = (t.stats_levels && t.stats_levels.length) || 180;
  const initRow = (t.stats_levels && t.stats_levels[initLv - 1]) || [0, 0, 0, 0, 0];

  dv.innerHTML = `
    <div class="patch-nav"><a class="preset-btn" href="/tamers">← เทมเมอร์ทั้งหมด (เซิร์ฟไทย)</a></div>
    <div class="panel tm-hero">
      <div class="tm-hero-art">
        <div class="tm-hero-portrait">
          <img src="${esc(t.portrait_lg || t.portrait_sm || PLACEHOLDER)}" alt="${esc(t.name_th)}" onerror="this.src='${PLACEHOLDER}'">
        </div>
      </div>
      <div class="tm-hero-main">
        <div class="tm-card-top" style="justify-content:flex-start;margin-bottom:8px">
          <span class="tm-tag ${t.starter ? 'starter' : 'unlock'}">${t.starter ? 'ตัวละครเริ่มต้น (เลือกสร้างได้ทันที)' : 'ตัวละครปลดล็อก / เปลี่ยนตัว'}</span>
          <span class="tm-tag">${esc(t.gender)}</span>
          <span class="tm-tag">${esc(t.series)} · ${esc(t.series_en)}</span>
          ${t.in_thai ? `<span class="tm-tag thai">มีข้อมูลในไคลเอนต์ไทย (${t.pack_files} ไฟล์โมเดล)</span>` : ''}
        </div>
        <h2>${esc(t.name_th)}</h2>
        <div style="color:var(--text-muted);font-size:0.95rem">${esc(t.name_en)}</div>
        ${t.partner ? `<div style="margin-top:8px;font-size:0.9rem;color:#7dd3fc">ดิจิมอนคู่หูประจำภาค: <strong>${esc(t.partner)}</strong> · แนวทางค่าพลัง: <strong>${esc(t.role)}</strong></div>` : ''}
        ${t.bio ? `<div class="tm-bio-box">${esc(t.bio)}</div>` : ''}
      </div>
    </div>

    <div class="tm-detail-grid">
      <div class="panel">
        <h3 class="panel-title">สเตตัสเทมเมอร์ตามเลเวล (Lv.1 – Lv.${initLv})</h3>
        <div class="tm-slider-wrap">
          <span class="tm-lv-badge" id="tm-lv-badge">Lv.${initLv}</span>
          <input id="tm-lv-slider" type="range" min="1" max="${initLv}" value="${initLv}" oninput="updateTamerStatLv(${t.id}, this.value)">
        </div>
        <div class="tm-lv-presets">
          ${[1, 50, 99, 120, 140, 150, 160, 170, 180].filter(v => v <= initLv).map(v =>
    `<button class="preset-btn" style="padding:4px 10px;font-size:0.78rem" onclick="updateTamerStatLv(${t.id}, ${v})">Lv.${v}</button>`
  ).join('')}
        </div>
        <div class="tm-stats-mini" style="margin-bottom:14px">
          <div><span>HP</span><strong id="tm-stat-hp">${fmtNum(initRow[0])}</strong></div>
          <div><span>DS</span><strong id="tm-stat-ds">${fmtNum(initRow[1])}</strong></div>
          <div><span>MS</span><strong id="tm-stat-ms">${fmtNum(initRow[2])}</strong></div>
          <div><span>AT</span><strong id="tm-stat-at">${fmtNum(initRow[4])}</strong></div>
          <div><span>DE</span><strong id="tm-stat-de">${fmtNum(initRow[3])}</strong></div>
        </div>
        <div class="table-responsive">
          <table class="custom-table">
            <thead><tr><th>Lv</th><th>HP</th><th>DS</th><th>MS</th><th>AT</th><th>DE</th></tr></thead>
            <tbody>
              ${(t.stats_milestones || []).map(m => `<tr><td><strong>${m.lv}</strong></td><td>${fmtNum(m.hp)}</td><td>${fmtNum(m.ds)}</td><td>${fmtNum(m.ms)}</td><td>${fmtNum(m.at)}</td><td>${fmtNum(m.de)}</td></tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <h3 class="panel-title">โมเดล 3D ตัวละคร (${esc(t.name_th)})</h3>
        <div id="tm-model-viewer-${t.id}" class="tm-model-wrap"></div>
      </div>
    </div>

    ${(t.unlock_items?.length || t.costumes?.length || t.id_cards?.length) ? `
      <div class="panel" style="margin-top:16px">
        <h3 class="panel-title">ไอเทมปลดล็อก · ชุดเริ่มต้น · แมกเนติก ID Card ประจำตัว</h3>
        ${(t.unlock_items && t.unlock_items.length) ? `
          <div class="filter-label" style="margin-bottom:6px">ไอเทมเปลี่ยนตัว / แพ็คเกจปลดล็อก</div>
          <div class="tm-item-grid" style="margin-bottom:14px">
            ${t.unlock_items.map(it => `<div class="tm-item-pill">${it.icon ? `<img src="${esc(it.icon)}" alt="" onerror="this.remove()">` : ''}<div><div style="font-weight:700">${esc(it.name)}</div><div class="muted" style="font-size:0.72rem">${esc(it.kind)}</div></div></div>`).join('')}
          </div>` : ''}
        ${(t.costumes && t.costumes.length) ? `
          <div class="filter-label" style="margin-bottom:6px">ชุดคอสทูมหน้าสร้างตัวละครเริ่มต้น</div>
          <div class="tm-item-grid" style="margin-bottom:14px">
            ${t.costumes.map(c => `<div class="tm-item-pill">${c.icon ? `<img src="${esc(c.icon)}" alt="" onerror="this.remove()">` : ''}<div><div style="font-weight:700">${esc(c.name)}</div><div class="muted" style="font-size:0.72rem">คอสทูม</div></div></div>`).join('')}
          </div>` : ''}
        ${(t.id_cards && t.id_cards.length) ? `
          <div class="filter-label" style="margin-bottom:6px">แมกเนติก ID Card เฉพาะตัว</div>
          <div class="tm-item-grid">
            ${t.id_cards.map(c => `<div class="tm-item-pill">${c.icon ? `<img src="${esc(c.icon)}" alt="" onerror="this.remove()">` : ''}<div><div style="font-weight:700">${esc(c.name)}</div><div class="muted" style="font-size:0.72rem">ID Card</div></div></div>`).join('')}
          </div>` : ''}
      </div>` : ''}
  `;
  initTamerModelViewer(t.id, t.model_url || `/models/tamers/${t.id}.glb`, {
    nif: t.model_nif || '',
    verts: t.model_verts || 0,
    tris: t.model_tris || 0
  });
  window.scrollTo({ top: 0 });
}

// ======================================================
// TAMER STATUS & 17-SLOT EQUIPMENT INTERACTIVE GUIDE
// ======================================================
const TM_STATUS_STATE = {
  activeWin: 1,
  selectedKey: 'earring',
  pendingRender: false,
};

function _getAllTamerEquipSlots(ts) {
  if (!ts) return [];
  return [
    ...(ts.slots || []),
    ...(ts.friendship_orb ? [ts.friendship_orb] : []),
    ...(ts.digimon_slots ? [ts.digimon_slots] : []),
    ...(ts.evo_chip_slots ? [ts.evo_chip_slots] : []),
    ...(ts.chipset_slot ? [ts.chipset_slot] : []),
  ];
}

function openTamerStatusView() {
  document.title = 'เทมเมอร์สเตตัส - DMO Thai Wiki';
  const host = document.getElementById('tm-status-view');
  if (!host) return;
  if (!STATE.tamers.statusData) {
    TM_STATUS_STATE.pendingRender = true;
    host.innerHTML = `<div class="panel" style="padding:28px;text-align:center">กำลังโหลดข้อมูล Interface Tamer Status...</div>`;
    loadTamers();
    return;
  }
  renderTamerStatusView();
}

function switchTamerStatusWin(winId) {
  TM_STATUS_STATE.activeWin = winId;
  if (winId === 2) {
    if (!['digimon_storage_8', 'evo_chip_2', 'chipset'].includes(TM_STATUS_STATE.selectedKey)) {
      TM_STATUS_STATE.selectedKey = 'digimon_storage_8';
    }
  } else if (winId === 3) {
    TM_STATUS_STATE.selectedKey = TM_STATUS_STATE.selectedSkillKey || 'b1_wait';
  } else if (winId === 1) {
    const slotKeys = new Set((STATE.tamers.statusData?.slots || []).map(s => s.key));
    slotKeys.add('friendship_orb');
    if (!slotKeys.has(TM_STATUS_STATE.selectedKey)) {
      TM_STATUS_STATE.selectedKey = 'earring';
    }
  }
  renderTamerStatusView();
}

function selectTamerEquipSlot(key, jumpScroll = false) {
  const ts = STATE.tamers.statusData;
  if (!ts) return;
  const skTab = ts.skill_tab || {};
  const tab3Keys = new Set([
    ...(skTab.basic_skills || []).map(b => b.key),
    skTab.active_section?.key || 'tamer_active_slot',
    skTab.passive_section?.key || 'tamer_passive_slot',
  ]);
  if (tab3Keys.has(key)) {
    TM_STATUS_STATE.activeWin = 3;
    TM_STATUS_STATE.selectedKey = key;
    TM_STATUS_STATE.selectedSkillKey = key;
    renderTamerStatusView();
    if (jumpScroll) {
      const el = document.getElementById('ts-main-board');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    return;
  }
  const target = _getAllTamerEquipSlots(ts).find(s => s.key === key);
  if (!target) return;
  TM_STATUS_STATE.selectedKey = key;
  if (key === 'digimon_storage_8' || key === 'evo_chip_2' || key === 'chipset') {
    TM_STATUS_STATE.activeWin = 2;
  } else {
    TM_STATUS_STATE.activeWin = 1;
  }
  renderTamerStatusView();
  if (jumpScroll) {
    const el = document.getElementById('ts-main-board');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function _renderHotspotRect(rect, active, opts) {
  const [x, y, w, h] = rect;
  const pct = (v, max) => ((v / max) * 100).toFixed(3) + '%';
  const color = opts.color || '#38bdf8';
  const iconHtml = opts.icon
    ? `<img class="ts-slot-thumb" src="${esc(opts.icon)}" alt="" onerror="this.remove()">`
    : '';
  const shapeCls = opts.hex ? 'ts-hotspot-hex' : '';
  return `
    <button type="button"
      class="ts-hotspot ${shapeCls} ${active ? 'active' : ''}"
      style="left:${pct(x, 406)};top:${pct(y, 676)};width:${pct(w, 406)};height:${pct(h, 676)};--slot-color:${color}"
      title="${esc(opts.title || '')}"
      onclick="selectTamerEquipSlot('${esc(opts.key)}')">
      ${iconHtml}
      ${opts.badge ? `<span class="ts-slot-num">${esc(String(opts.badge))}</span>` : ''}
    </button>`;
}

function renderTamerStatusView() {
  const host = document.getElementById('tm-status-view');
  const ts = STATE.tamers.statusData;
  if (!host || !ts) return;

  const allSlots = _getAllTamerEquipSlots(ts);
  const selected = allSlots.find(s => s.key === TM_STATUS_STATE.selectedKey) || allSlots[0];
  const curWin = (ts.win_tabs || []).find(w => w.id === TM_STATUS_STATE.activeWin) || ts.win_tabs[0];
  const skTab = ts.skill_tab || {};
  const basicList = skTab.basic_skills || [];

  // Build pixel-aligned hotspots per tab (406x676 canvas)
  let overlays = '';
  if (TM_STATUS_STATE.activeWin === 1) {
    const fo = ts.friendship_orb;
    overlays = (ts.slots || []).map(s => _renderHotspotRect(s.rect, s.key === selected.key, {
      key: s.key,
      badge: s.num,
      title: `${s.num}. ${s.name_th} — คลิกเพื่อดูรายละเอียด`,
      color: s.color,
    })).join('') + (fo ? _renderHotspotRect(fo.rect, fo.key === selected.key, {
      key: fo.key,
      badge: fo.num,
      title: `${fo.name_th} — คลิกเพื่อดูเงื่อนไขการเพิ่ม/ลดค่าความสนิท`,
      color: fo.color,
      hex: true,
    }) : '');
  } else if (TM_STATUS_STATE.activeWin === 2) {
    const dg = ts.digimon_slots;
    const ec = ts.evo_chip_slots;
    const ch = ts.chipset_slot;
    overlays =
      (dg ? dg.rects.map((r, idx) => _renderHotspotRect(r, selected.key === 'digimon_storage_8', {
        key: 'digimon_storage_8',
        badge: `D${idx + 1}`,
        title: `ช่องเก็บดิจิมอนพกพา D${idx + 1} / 8 (ช่องว่าง — คลิกเพื่อดูรายละเอียด)`,
        color: dg.color,
        hex: true,
      })).join('') : '') +
      (ec ? ec.rects.map((r, idx) => _renderHotspotRect(r, selected.key === 'evo_chip_2', {
        key: 'evo_chip_2',
        badge: `J${idx + 1}`,
        title: idx === 0 ? 'ช่องชิพแปลงร่าง (ดิจิครอสชิป / โจเกรสชิป) — ไม่เกี่ยวกับชิปเซ็ท' : 'ช่องชิพแปลงร่าง (ชิพโจเกรส / ดิจิครอสชิป) — ไม่เกี่ยวกับชิปเซ็ท',
        color: ec.color,
      })).join('') : '') +
      (ch ? ch.rects.map((r, idx) => _renderHotspotRect(r, selected.key === 'chipset', {
        key: 'chipset',
        badge: `C${idx + 1}`,
        title: `ช่องชิปเซ็ท C${idx + 1} / 8 (คลิกเพื่อดูรายละเอียด)`,
        color: ch.color,
      })).join('') : '');
  } else if (TM_STATUS_STATE.activeWin === 3) {
    const activeSec = skTab.active_section;
    const passiveSec = skTab.passive_section;
    overlays =
      basicList.map((bs, idx) => _renderHotspotRect(bs.rect, TM_STATUS_STATE.selectedKey === bs.key, {
        key: bs.key,
        badge: bs.badge || `B${idx + 1}`,
        title: `${bs.name_th} — คลิกดูรายละเอียด`,
        color: bs.is_blank_swap ? '#fbbf24' : '#38bdf8',
        icon: bs.is_blank_swap ? '' : (bs.icon || ''),
      })).join('') +
      (activeSec ? _renderHotspotRect(activeSec.rects[0], TM_STATUS_STATE.selectedKey === activeSec.key, {
        key: activeSec.key,
        badge: 'Act',
        title: activeSec.title,
        color: '#a855f7',
      }) : '') +
      (passiveSec ? _renderHotspotRect(passiveSec.rects[0], TM_STATUS_STATE.selectedKey === passiveSec.key, {
        key: passiveSec.key,
        badge: 'P1',
        title: passiveSec.title,
        color: '#22c55e',
        icon: passiveSec.base_icon || '',
      }) : '');
  }

  const stoneInfo = selected.stone_key && ts.stones ? ts.stones[selected.stone_key] : null;
  const leftSlots = (ts.slots || []).filter(s => s.num <= 9);
  const rightSlots = (ts.slots || []).filter(s => s.num >= 10);
  const cleanDetails = (selected.details || '').replace(/\s*\(\*หมายเหตุ:[^)]*\)/g, '').trim();

  let rightPanelHtml = '';
  if (TM_STATUS_STATE.activeWin === 3) {
    const pickedBasic = basicList.find(b => b.key === TM_STATUS_STATE.selectedKey);
    const activeSec = skTab.active_section || {};
    const passiveSec = skTab.passive_section || {};
    let focusTitle = pickedBasic ? pickedBasic.name_th : (TM_STATUS_STATE.selectedKey === 'tamer_active_slot' ? activeSec.title : TM_STATUS_STATE.selectedKey === 'tamer_passive_slot' ? passiveSec.title : (basicList[0]?.name_th || 'สกิลเทมเมอร์'));
    let focusDesc = pickedBasic ? pickedBasic.desc : (TM_STATUS_STATE.selectedKey === 'tamer_active_slot' ? activeSec.desc : TM_STATUS_STATE.selectedKey === 'tamer_passive_slot' ? passiveSec.desc : (basicList[0]?.desc || ''));
    let focusBadge = pickedBasic ? (pickedBasic.is_blank_swap ? 'ช่องเปลี่ยนดิจิมอน' : 'สกิลพื้นฐาน') : (TM_STATUS_STATE.selectedKey === 'tamer_active_slot' ? 'สกิลใช้งาน (Active)' : 'สกิลติดตัว (Passive)');

    rightPanelHtml = `
      <div class="ts-detail-head">
        <div class="ts-detail-badges">
          <span class="ts-badge-num" style="background:#38bdf8">${esc(focusBadge)}</span>
          <span class="tm-tag thai">หน้าต่างสกิล (Tab 3)</span>
        </div>
        <h2 class="ts-detail-title">${esc(focusTitle)}</h2>
      </div>

      <div class="ts-detail-box">
        <div class="ts-sec-label">คำอธิบายสกิล / ช่องที่เลือก</div>
        <p class="ts-desc">${esc(focusDesc)}</p>
      </div>

      <div class="ts-detail-box">
        <div class="ts-sec-label">สกิลพื้นฐานของเทมเมอร์ทั้งหมด (4 คำสั่ง + 5 ช่องว่างเปลี่ยนดิจิมอน + AFK)</div>
        <div class="ts-skill-list">
          ${basicList.map((bs, idx) => {
      const bTag = bs.badge || `B${idx + 1}`;
      return `
              <button type="button" class="ts-skill-row ${TM_STATUS_STATE.selectedKey === bs.key ? 'active' : ''}" onclick="selectTamerEquipSlot('${esc(bs.key)}')">
                <div class="ts-skill-ico">${(!bs.is_blank_swap && bs.icon) ? `<img src="${esc(bs.icon)}" alt="" onerror="this.remove()">` : `<span style="font-size:0.74rem;font-weight:800;color:#fbbf24">${esc(bTag)}</span>`}</div>
                <div class="ts-skill-info">
                  <div class="ts-skill-name">${esc(bTag)}. ${esc(bs.name_th)}</div>
                  <div class="ts-skill-desc">${esc(bs.desc)}</div>
                </div>
              </button>`;
    }).join('')}
        </div>
      </div>

      <div class="ts-detail-box">
        <div class="ts-sec-label">หมวดสกิลใช้งาน &amp; สกิลติดตัว (Active &amp; Passive Slots)</div>
        <div style="display:grid;gap:8px;font-size:0.82rem;color:var(--text-sub);line-height:1.55">
          <div><strong style="color:#c084fc">• สกิลใช้งาน (Active):</strong> ${esc(activeSec.desc || '')}</div>
          <div><strong style="color:#4ade80">• สกิลติดตัว (Passive):</strong> ${esc(passiveSec.desc || '')}</div>
          <div><a href="/tamers" style="color:#38bdf8;font-weight:700">ดูตารางสกิล Active / Passive ทั้งหมดจากกล่องซาสึมะ →</a></div>
        </div>
      </div>
    `;
  } else {
    const badgeText = selected.key === 'friendship_orb' ? 'ลูกแก้วความสนิทสนม' : `ช่องที่ ${selected.num}`;
    rightPanelHtml = `
      <div class="ts-detail-head" style="--slot-color:${selected.color}">
        <div class="ts-detail-badges">
          <span class="ts-badge-num" style="background:${selected.color}">${esc(badgeText)}</span>
          <span class="tm-tag">${esc(selected.side)}</span>
        </div>
        <h2 class="ts-detail-title">${esc(selected.name_th)}</h2>
        <div class="muted" style="font-size:0.86rem">${esc(selected.name_en)} · หมวดในเกม: <code>${esc(selected.category)}</code></div>
      </div>

      <div class="ts-detail-box">
        <div class="ts-sec-label">${selected.key === 'friendship_orb' ? 'ลูกแก้วนี้คืออะไร / เงื่อนไขทำงาน?' : 'ช่องนี้มีไว้ทำอะไร / ใส่อะไร?'}</div>
        <p class="ts-desc" style="white-space:pre-line">${esc(cleanDetails)}</p>
      </div>

      <div class="ts-detail-box">
        <div class="ts-sec-label">หน้าที่และผลลัพธ์หลักที่ได้จากช่องนี้</div>
        <div class="ts-stat-highlight">${esc(selected.stats_note)}</div>
      </div>

      ${stoneInfo ? `
        <div class="ts-detail-box ts-stone-box">
          <div class="ts-sec-label">ระบบเสริมพลัง / หินเสริมของช่องนี้</div>
          <div style="font-size:0.85rem;color:var(--text-main);line-height:1.6">
            <strong>${esc(stoneInfo.title)}</strong> — <span style="color:#4ade80">${esc(stoneInfo.badge)}</span>
          </div>
        </div>
      ` : ''}
    `;
  }

  const renderSlotListCard = s => {
    const active = s.key === selected.key;
    return `
      <button type="button" class="ts-ref-card ${active ? 'active' : ''}" style="--slot-color:${s.color}" onclick="selectTamerEquipSlot('${esc(s.key)}', true)">
        <div class="ts-ref-num">${s.num}</div>
        <div class="ts-ref-body">
          <div class="ts-ref-title">${esc(s.name_th)}</div>
          <div class="ts-ref-sub">${esc(s.summary)}</div>
          <div class="ts-ref-meta">
            <span>หมวด: ${esc(s.category)}</span>
          </div>
        </div>
      </button>`;
  };

  host.innerHTML = `
    <div class="panel tm-satsuma-banner" style="margin-bottom:14px">
      <div class="tm-sat-head">
        <div>
          <h3 style="margin:0 0 4px;font-size:1.12rem;color:#38bdf8">หน้าต่าง Tamer Status &amp; คำอธิบายทุกช่อง (17 อุปกรณ์ · 8 เก็บดิจิมอน · 2 ชิพแปลงร่าง · 8 ชิปเซ็ท · สกิล)</h3>
          <div class="muted" style="font-size:0.84rem">ใช้ภาพ Interface จริงจากไคลเอนต์ DMO เซิร์ฟไทย — <strong>คลิกที่ช่องบนรูปหน้าต่างเกม</strong> หรือกดเลือกการ์ดด้านล่างเพื่อดูรายละเอียดว่าแต่ละช่องมีไว้ทำอะไร</div>
        </div>
      </div>
    </div>

    <div id="ts-main-board" class="ts-board">
      <div class="panel ts-window-col">
        <div class="ts-win-tabs">
          ${(ts.win_tabs || []).map(w => `
            <button type="button" class="ts-win-tab ${w.id === TM_STATUS_STATE.activeWin ? 'active' : ''}" onclick="switchTamerStatusWin(${w.id})">${esc(w.label)}</button>
          `).join('')}
        </div>

        <div class="ts-canvas-wrap">
          <div class="ts-canvas" style="aspect-ratio:${ts.canvas.w} / ${ts.canvas.h}">
            <img class="ts-canvas-bg" src="${esc(curWin.img)}" alt="Tamer Status UI">
            ${overlays}
          </div>
        </div>

        ${TM_STATUS_STATE.activeWin === 1 ? `
          <div class="ts-bar-guide">
            <div class="ts-bar-title">ส่วนล่างของหน้าต่าง: ค่าความสนิทสนม &amp; ค่าความสามารถเพิ่มเติม</div>
            <div style="font-size:0.78rem;color:var(--text-sub);line-height:1.5;margin-bottom:8px">
              • <strong style="color:#4ade80">ลูกแก้วตรงกลาง / แถบซ้าย (ค่าความสนิทสนม)</strong>: ยิ่งมาก ดิจิมอนคู่หูยิ่งเก่งขึ้น (สู้ทุก 2 นาที +1 / อยู่นิ่งทุก 5 นาที -5 / แพ้รีเซ็ตค่าเริ่ม / สูงสุด 35 หรือ 60 ด้วยไอเทม)
              <button type="button" class="preset-btn" style="padding:2px 8px;font-size:0.74rem;margin-left:4px" onclick="selectTamerEquipSlot('friendship_orb')">ดูรายละเอียดเต็ม →</button>
            </div>
            <div class="ts-bar-grid">
              <div><strong style="color:#f87171">AT</strong> : ค่าความสามารถเพิ่มเติม (โจมตี)</div>
              <div><strong style="color:#60a5fa">DE</strong> : ค่าความสามารถเพิ่มเติม (ป้องกัน)</div>
              <div><strong style="color:#4ade80">HP</strong> : ค่าความสามารถเพิ่มเติม (เลือด)</div>
              <div><strong style="color:#38bdf8">DS</strong> : ค่าความสามารถเพิ่มเติม (DigiSoul)</div>
            </div>
          </div>
        ` : TM_STATUS_STATE.activeWin === 2 ? `
          <div class="ts-bar-guide">
            <div class="ts-bar-title">แท็บ 2: เก็บดิจิมอน 8 ช่อง · ชิพโจเกรส/ดิจิครอส 2 ช่อง · ชิปเซ็ท 8 ช่อง</div>
            <div style="font-size:0.78rem;color:var(--text-sub);line-height:1.5">
              • <strong>D1–D8 (หกเหลี่ยม 8 ช่อง)</strong>: เก็บดิจิมอนพกพา (คลิกขวา: เปลี่ยนพาร์ทเนอร์ / ลบ)<br>
              • <strong>J1–J2 (ตรงกลาง 2 ช่อง)</strong>: ใส่ชิพโจเกรส / ดิจิครอสชิป เพื่อแปลงร่างเท่านั้น<br>
              • <strong>C1–C8 (แถวล่าง 8 ช่อง)</strong>: ใส่ชิปเซ็ทเพิ่มสเตตัส (แยกจากชิพตรงกลาง)
            </div>
          </div>
        ` : `
          <div class="ts-bar-guide">
            <div class="ts-bar-title">แท็บ 3: สกิลเทมเมอร์ (Basic · Active · Passive)</div>
            <div style="font-size:0.78rem;color:var(--text-sub);line-height:1.5">
              แถวบน <strong>สกิลพื้นฐาน (B1–B4, 5 ช่องว่างเปลี่ยนดิจิมอน S1–S5, AFK)</strong> · แถวกลาง <strong>สกิลใช้งาน (1 ช่อง)</strong> · แถวล่าง <strong>สกิลติดตัว (วิ่งเร็ว + 2 ช่องเฉพาะ)</strong>
            </div>
          </div>
        `}
      </div>

      <div class="panel ts-detail-col">${rightPanelHtml}</div>
    </div>

    <div class="panel" style="margin-top:16px">
      <h3 class="panel-title" style="margin-bottom:12px">สรุปครบทุกช่อง (17 อุปกรณ์ + 8 เก็บดิจิมอน + 2 ชิพแปลงร่าง + 8 ชิปเซ็ท — กดการ์ดเพื่อโฟกัส)</h3>
      <div class="ts-ref-columns">
        <div>
          <div class="ts-col-header">ฝั่งซ้าย — ชุดอุปกรณ์ เครื่องแต่งกาย &amp; ป้ายชื่อ (ช่อง 1–9)</div>
          <div class="ts-ref-list">${leftSlots.map(renderSlotListCard).join('')}</div>
        </div>
        <div>
          <div class="ts-col-header">ฝั่งขวา — เครื่องประดับ ดิจิไวซ์ ช่องดิจิมอน &amp; ชิพ (ช่อง 10–20)</div>
          <div class="ts-ref-list">
            ${rightSlots.map(renderSlotListCard).join('')}
            ${ts.digimon_slots ? renderSlotListCard(ts.digimon_slots) : ''}
            ${ts.evo_chip_slots ? renderSlotListCard(ts.evo_chip_slots) : ''}
            ${ts.chipset_slot ? renderSlotListCard(ts.chipset_slot) : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

// ==========================================
// SEAL MASTER MODULE (สารานุกรมดิจิมอน -> ซีลมาสเตอร์)
// ==========================================
const SEAL_STATE = {
  loaded: false,
  loading: null,
  items: [],
  statTotals: [],
  worlds: [],
  maps: [],
  rules: {},
  stat: 'all',
  source: 'all',
  mapId: '',
  currentSeal: null,
};

const SEAL_SOURCE_PILLS = [
  { key: 'all', label: 'ทั้งหมด' },
  { key: 'drop', label: 'ดรอปตามแมพ' },
  { key: 'exchange', label: 'แลกเปลี่ยน / คราฟต์ NPC' },
  { key: 'card', label: 'การ์ดมอนสเตอร์' },
  { key: 'pack', label: 'แพ็ก / กล่องสุ่ม' },
  { key: 'event', label: 'กิจกรรม' },
];

async function loadSeals() {
  if (SEAL_STATE.loaded) return SEAL_STATE.items;
  if (SEAL_STATE.loading) return SEAL_STATE.loading;
  const grid = document.getElementById('seal-grid');
  if (grid && !grid.innerHTML.trim()) grid.innerHTML = SKEL.eggs ? SKEL.eggs(8) : '<div class="loading">กำลังโหลดข้อมูลซีลมาสเตอร์...</div>';

  SEAL_STATE.loading = (async () => {
    try {
      const resp = await fetch('/api/seals');
      const data = await resp.json();
      SEAL_STATE.items = data.items || [];
      SEAL_STATE.statTotals = data.stat_totals || [];
      SEAL_STATE.worlds = data.worlds || [];
      SEAL_STATE.maps = data.maps || [];
      SEAL_STATE.rules = data.opener_closer_rules || {};
      SEAL_STATE.loaded = true;
      buildSealControls();
      renderSealsList();
    } catch (e) {
      SEAL_STATE.items = [];
      if (grid) grid.innerHTML = '<div class="empty-state">โหลดข้อมูลซีลมาสเตอร์ไม่สำเร็จ</div>';
    } finally {
      SEAL_STATE.loading = null;
    }
    return SEAL_STATE.items;
  })();
  return SEAL_STATE.loading;
}

function buildSealControls() {
  const statPills = document.getElementById('seal-stat-pills');
  if (statPills) {
    const allCount = SEAL_STATE.items.length;
    const html = [
      `<button class="filter-pill seal-stat-pill ${SEAL_STATE.stat === 'all' ? 'active' : ''}" onclick="SEAL_STATE.stat='all'; buildSealControls(); renderSealsList()">ทั้งหมด <span class="seal-stat-cap">${allCount}</span></button>`,
      ...SEAL_STATE.statTotals.map(st => `
        <button class="filter-pill seal-stat-pill ${SEAL_STATE.stat === st.key ? 'active' : ''}"
          onclick="SEAL_STATE.stat='${st.key}'; buildSealControls(); renderSealsList()">
          <span>${esc(st.key)} · ${esc(st.name_th)}</span>
          <span class="seal-stat-cap">${esc(st.max_total_display)} (${st.count})</span>
        </button>`),
    ];
    statPills.innerHTML = html.join('');
  }

  const srcPills = document.getElementById('seal-src-pills');
  if (srcPills) {
    srcPills.innerHTML = SEAL_SOURCE_PILLS.map(p => `
      <button class="filter-pill ${SEAL_STATE.source === p.key ? 'active' : ''}"
        onclick="SEAL_STATE.source='${p.key}'; buildSealControls(); renderSealsList()">${p.label}</button>
    `).join('');
  }

  const mapSel = document.getElementById('seal-map-select');
  if (mapSel && mapSel.options.length <= 1) {
    const grouped = new Map();
    for (const m of SEAL_STATE.maps) {
      if (!grouped.has(m.world_name)) grouped.set(m.world_name, []);
      grouped.get(m.world_name).push(m);
    }
    let opts = `<option value="">ทุกแมพในเกม (${SEAL_STATE.maps.length} แมพ)</option>`;
    for (const [wname, mlist] of grouped.entries()) {
      opts += `<optgroup label="${esc(wname)}">`;
      for (const m of mlist) {
        opts += `<option value="${m.map_id}">${esc(m.map_name)} (${m.count})</option>`;
      }
      opts += '</optgroup>';
    }
    mapSel.innerHTML = opts;
    if (SEAL_STATE.mapId) mapSel.value = String(SEAL_STATE.mapId);
  }

  const banner = document.getElementById('seal-rules-banner');
  if (banner) {
    const r = SEAL_STATE.rules;
    banner.innerHTML = `
      <div class="seal-rule-card">
        <img src="${esc(r.opener_icon || '/images/Seal_Opener_Icon.png')}" alt="การ์ดเปิดผนึก" onerror="this.style.display='none'">
        <div>
          <div><strong>การ์ดเปิดผนึก (Seal Opener)</strong> — <strong>1 ใบ</strong> เปิดผนึกได้ <strong>50 ซีล</strong></div>
          <div>${esc(r.opener_rule_th || 'เปิดขั้นแรก 1–49 ใบใช้ขั้นต่ำ 1 ใบ · เปิดครบ Master 3,000 ใบใช้ 60 ใบ')}</div>
        </div>
      </div>
      <div class="seal-rule-card">
        <img src="${esc(r.closer_icon || '/images/Seal_Closer_Icon.png')}" alt="การ์ดปิดผนึก" onerror="this.style.display='none'">
        <div>
          <div><strong>การ์ดปิดผนึก (Seal Closer)</strong> — <strong>1 ใบ</strong> ถอด/ปิดผนึกได้ <strong>50 ซีล</strong></div>
          <div>${esc(r.closer_rule_th || 'ปิดผนึกกี่ใบ ได้รับซีลกลับเข้ากระเป๋าคืนครบเต็มจำนวน 1:1 เพื่อนำไปแลกเปลี่ยนได้')}</div>
        </div>
      </div>`;
  }
}

function renderSealsList() {
  const grid = document.getElementById('seal-grid');
  if (!grid) return;
  const qEl = document.getElementById('seal-search-input');
  const q = (qEl ? qEl.value : '').trim().toLowerCase();
  const stFilter = SEAL_STATE.stat;
  const srcFilter = SEAL_STATE.source;
  const mapFilter = SEAL_STATE.mapId ? Number(SEAL_STATE.mapId) : 0;

  const list = SEAL_STATE.items.filter(s => {
    if (stFilter !== 'all' && s.stat_key !== stFilter) return false;
    if (srcFilter !== 'all' && !(s.source_categories || []).includes(srcFilter)) return false;
    if (mapFilter && !(s.hunting_maps || []).some(m => m.map_id === mapFilter)) return false;
    if (q) {
      const hay = [
        s.name_th, s.name_en, s.stat_key, s.stat_name_th,
        ...(s.hunting_maps || []).map(m => `${m.map_name} ${m.world_name}`),
        ...(s.crafts || []).map(c => `${c.npc} ${(c.materials || []).map(x => x.name).join(' ')}`),
        ...(s.extra_notes || []),
        s.wiki_drop_en || '',
      ].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  // Update live filtered totals
  let countStrip = document.getElementById('seal-count-strip');
  if (!countStrip) {
    countStrip = document.createElement('div');
    countStrip.id = 'seal-count-strip';
    countStrip.className = 'seal-count-strip';
    grid.parentNode.insertBefore(countStrip, grid);
  }

  let statSummaryText = '';
  if (stFilter !== 'all') {
    const isPct = list[0]?.is_pct || false;
    const sumVal = list.reduce((acc, s) => acc + (s.master_stat_value || 0), 0);
    const sumSeals = list.reduce((acc, s) => acc + (s.master_seals || 0), 0);
    const sumOpeners = list.reduce((acc, s) => acc + (s.master_openers || 0), 0);
    const fmtVal = isPct ? `+${(sumVal / 100).toFixed(2).replace(/\.?0+$/, '')}%` : `+${sumVal.toLocaleString()}`;
    statSummaryText = `โบนัส Master รวมหมวด ${stFilter}: <strong style="color:#38bdf8">${fmtVal}</strong> (ใช้ซีลรวม ${sumSeals.toLocaleString()} ใบ · การ์ดเปิดผนึก ${sumOpeners.toLocaleString()} ใบ)`;
  } else {
    statSummaryText = 'คลิกที่การ์ดซีลเพื่อดูขั้นปลดล็อกทั้ง 6 ขั้น แมพดรอป และการคำนวณการ์ดเปิด/ปิดผนึก';
  }
  countStrip.innerHTML = `<div>พบ: <strong style="color:var(--color-primary)">${list.length}</strong> / ${SEAL_STATE.items.length} ซีล</div><div>${statSummaryText}</div>`;

  if (!list.length) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1">ไม่พบซีลที่ตรงกับเงื่อนไขการค้นหา</div>';
    return;
  }

  const cardsHtml = list.map(s => {
    const mapChips = (s.hunting_maps || []).slice(0, 2).map(m => `<span class="seal-src-chip">${esc(m.map_name)}</span>`);
    if ((s.hunting_maps || []).length > 2) mapChips.push(`<span class="seal-src-chip">+${s.hunting_maps.length - 2} แมพ</span>`);
    if (s.crafts && s.crafts.length) {
      const c0 = s.crafts[0];
      const mat0 = c0.materials && c0.materials[0];
      if (mat0) mapChips.push(`<span class="seal-src-chip is-craft">${esc(mat0.name)} ×${mat0.qty} → ${c0.out_qty} ใบ</span>`);
    }
    if (!mapChips.length && (s.extra_notes || []).length) {
      mapChips.push(`<span class="seal-src-chip is-event">${esc(s.extra_notes[0])}</span>`);
    }
    if (!mapChips.length && (s.hub_sources || []).length) {
      mapChips.push(`<span class="seal-src-chip">${esc(s.hub_sources[0].map_name)}</span>`);
    }

    const normalTier = (s.tiers || [])[0];
    return `
      <a class="seal-card" href="/seal/${encodeURIComponent(s.slug)}"
        onclick="event.preventDefault(); navigateTo('seal/' + encodeURIComponent('${s.slug.replace(/'/g, "\\'")}'))">
        <div class="seal-card-top">
          <span class="seal-stat-badge stat-${esc(s.stat_key)}">${esc(s.stat_key)} ${esc(s.master_stat_display)}</span>
          <span style="font-size:0.74rem;color:var(--text-muted)">เริ่มต้น ${normalTier ? esc(normalTier.stat_display) : ''}</span>
        </div>
        <div class="seal-card-body">
          <div class="seal-art-frame">
            <img class="seal-art-img" loading="lazy" src="${esc(s.image)}" alt="${esc(s.name_th)}" onerror="this.src='/images/Seal_Icon.png'">
            <img class="seal-frame-overlay" src="/images/sealmaster/sealback/sealmaster_bg_master2.png" alt="">
            ${s.element_icon ? `<img class="seal-elem-icon" src="${esc(s.element_icon)}" title="${esc(s.element_name)}" alt="">` : ''}
          </div>
          <div style="min-width:0;flex:1">
            <div class="seal-card-title">${esc(s.name_th)}</div>
            ${s.name_en && s.name_en.toLowerCase() !== s.name_th.toLowerCase() ? `<div class="seal-card-en">${esc(s.name_en)}</div>` : ''}
            <div class="seal-mini-req">
              <span class="seal-mini-pill">Master: <strong>${s.master_seals.toLocaleString()}</strong> ใบ</span>
              <span class="seal-mini-pill">เปิดผนึก: <strong>${s.master_openers}</strong> ใบ</span>
              <span class="seal-mini-pill">ปิดผนึก: <strong>${s.master_closers}</strong> ใบ</span>
            </div>
          </div>
        </div>
        <div class="seal-card-sources">${mapChips.join('')}</div>
      </a>`;
  }).join('');
  grid.innerHTML = cardsHtml;
}

async function openSeal(slugOrId) {
  const listView = document.getElementById('seal-list-view');
  const detailEl = document.getElementById('seal-detail');
  if (listView) listView.style.display = 'none';
  if (detailEl) {
    detailEl.style.display = '';
    detailEl.innerHTML = '<div class="loading">กำลังโหลดรายละเอียดซีล...</div>';
  }
  await loadSeals();
  const key = String(slugOrId || '').trim().toLowerCase();
  let seal = SEAL_STATE.items.find(s => s.slug.toLowerCase() === key || String(s.id) === key || s.name_th.toLowerCase() === key || s.name_en.toLowerCase() === key);
  if (!seal) {
    try {
      const r = await fetch(`/api/seals/${encodeURIComponent(slugOrId)}`);
      if (r.ok) {
        const j = await r.json();
        seal = j.seal;
      }
    } catch (e) { }
  }
  if (!seal) {
    if (detailEl) detailEl.style.display = 'none';
    showNotFoundPage('seal/' + slugOrId, `ไม่พบข้อมูลซีล "${slugOrId}" ในระบบ`);
    return;
  }
  SEAL_STATE.currentSeal = seal;
  renderSealDetail(seal);
}

function closeSeal(skipNav) {
  if (typeof disposeSealLeaderViewer === 'function') disposeSealLeaderViewer();
  SEAL_STATE.currentSeal = null;
  const listView = document.getElementById('seal-list-view');
  const detailEl = document.getElementById('seal-detail');
  if (detailEl) detailEl.style.display = 'none';
  if (listView) listView.style.display = '';
  loadSeals();
}

function renderSealDetail(s) {
  const detailEl = document.getElementById('seal-detail');
  if (!detailEl) return;
  const r = SEAL_STATE.rules || {};
  const openerIcon = r.opener_icon || '/images/Seal_Opener_Icon.png';
  const closerIcon = r.closer_icon || '/images/Seal_Closer_Icon.png';
  const normalTier = s.tiers[0] || { min_seals: 1, stat_display: s.master_stat_display, openers_total_direct: 1 };

  const tierRows = s.tiers.map(t => {
    const rawInfo = s.is_pct ? ` <span style="color:var(--text-muted);font-size:0.75rem">(ค่าดิบ +${t.stat_value})</span>` : '';
    return `
      <tr>
        <td>
          <span class="seal-tier-badge">
            <span class="seal-tier-swatch" style="background:${esc(t.color)}"></span>
            <span>${esc(t.name_en)} <span style="color:var(--text-muted);font-weight:500">(${esc(t.name_th)})</span></span>
          </span>
        </td>
        <td><strong>${t.min_seals.toLocaleString()}</strong> ใบ <span style="color:var(--text-muted);font-size:0.76rem">(ช่วง ${esc(t.range_text)})</span></td>
        <td>${t.tier === 0 ? '+1 (เริ่มต้น)' : `+${t.seals_delta.toLocaleString()} ใบ`}</td>
        <td><strong style="color:${esc(t.color)}">${esc(t.stat_display)}</strong>${rawInfo} <span style="color:var(--text-muted);font-size:0.75rem">(เพิ่ม ${esc(t.stat_delta_display)})</span></td>
        <td>
          <strong>${t.openers_total_direct}</strong> ใบ
          ${t.tier > 0 && t.seals_delta > 0 ? `<span style="color:var(--text-muted);font-size:0.75rem">(+ขั้นนี้ ${t.openers_step_batch} ใบ)</span>` : `<span style="color:var(--text-muted);font-size:0.75rem">(ขั้นต่ำ 1 ใบ)</span>`}
        </td>
        <td>
          ใช้ <strong>${t.closers_to_unequip}</strong> ใบ → ได้ซีลกลับ <strong>${t.seals_returned_on_close.toLocaleString()}</strong> ใบ
        </td>
      </tr>`;
  }).join('');

  const mapsHtml = (s.hunting_maps || []).length
    ? s.hunting_maps.map(m => `
        <div class="seal-map-row">
          <span><strong>${esc(m.map_name)}</strong></span>
          <span style="color:var(--text-muted);font-size:0.76rem">${esc(m.world_name)}</span>
        </div>`).join('')
    : '<div style="color:var(--text-muted);font-size:0.83rem">ไม่ดรอปตามแมพทั่วไป (หาจากแลกเปลี่ยน / การ์ด / กล่อง / กิจกรรม)</div>';

  const craftsHtml = (s.crafts || []).length
    ? s.crafts.map(c => {
      const mats = (c.materials || []).map(mt => `${esc(mt.name)} ×${mt.qty}`).join(' + ');
      const costTxt = c.cost_bit > 0 ? ` · ค่าใช้จ่าย ${c.cost_bit.toLocaleString()} B` : '';
      return `
          <div class="seal-map-row">
            <div>
              <div><strong>${esc(c.npc)}</strong></div>
              <div style="font-size:0.77rem;color:var(--text-sub)">ใช้: ${mats}${costTxt}</div>
            </div>
            <span class="seal-src-chip is-craft">ได้ ${c.out_qty} ใบ</span>
          </div>`;
    }).join('')
    : '<div style="color:var(--text-muted);font-size:0.83rem">ไม่มีสูตรแลกเปลี่ยนจาก NPC</div>';

  const extraList = [
    ...(s.extra_notes || []),
    ...(s.hub_sources || []).map(h => h.map_name),
  ];
  const uniqExtra = [...new Set(extraList)];
  const extraHtml = uniqExtra.length
    ? uniqExtra.map(n => `<div class="seal-map-row"><span>${esc(n)}</span></div>`).join('')
    : '<div style="color:var(--text-muted);font-size:0.83rem">ดูที่แมพดรอปหรือ NPC แลกเปลี่ยนด้านซ้าย</div>';

  const presetBtns = s.tiers.map(t =>
    `<button type="button" class="filter-pill" onclick="document.getElementById('seal-calc-qty').value=${t.min_seals}; updateSealCalculator()">${esc(t.name_en)} (${t.min_seals.toLocaleString()})</button>`
  ).join('');

  detailEl.innerHTML = `
    <div class="seal-detail-wrap">
      <div><button class="seal-back-btn" onclick="navigateTo('seals')">← กลับไปหน้าซีลมาสเตอร์</button></div>

      <div class="seal-hero-card">
        <div class="seal-art-frame large">
          <img class="seal-art-img" src="${esc(s.image)}" alt="${esc(s.name_th)}" onerror="this.src='/images/Seal_Icon.png'">
          <img class="seal-frame-overlay" src="/images/sealmaster/sealback/sealmaster_bg_master2.png" alt="">
          ${s.element_icon ? `<img class="seal-elem-icon" src="${esc(s.element_icon)}" title="${esc(s.element_name)}" alt="">` : ''}
        </div>
        <div class="seal-hero-info">
          <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:6px">
            <span class="seal-stat-badge stat-${esc(s.stat_key)}">${esc(s.stat_key)} · ${esc(s.stat_name_th)} (Master ${esc(s.master_stat_display)})</span>
            ${s.element_name ? `<span class="seal-mini-pill">ธาตุ: ${esc(s.element_name)}</span>` : ''}
            ${s.is_event ? `<span class="seal-src-chip is-event">กิจกรรม / พิเศษ</span>` : ''}
          </div>
          <h2 class="seal-hero-title">${esc(s.name_th)}</h2>
          ${s.name_en && s.name_en.toLowerCase() !== s.name_th.toLowerCase() ? `<div class="seal-hero-sub">${esc(s.name_en)} Seal</div>` : ''}
          ${s.description_th ? `<div class="seal-hero-desc">${esc(s.description_th)}</div>` : ''}
        </div>
      </div>

      <div id="seal-leader-viewer" class="seal-leader-panel"></div>

      <div class="seal-summary-kpis">
        <div class="seal-kpi">
          <div class="seal-kpi-label"><img src="/images/ui/ui_seal.png" class="stat-icon-inline" alt=""> จำนวนซีลสู่ระดับ Master</div>
          <div class="seal-kpi-val" style="color:#c084fc">${s.master_seals.toLocaleString()} ใบ</div>
          <div class="seal-kpi-sub">สเตตัสสูงสุด: <strong>${esc(s.stat_key)} ${esc(s.master_stat_display)}</strong></div>
        </div>
        <div class="seal-kpi">
          <div class="seal-kpi-label"><img src="${esc(openerIcon)}" alt=""> การ์ดเปิดผนึก (ถึง Master)</div>
          <div class="seal-kpi-val" style="color:#38bdf8">${s.master_openers.toLocaleString()} ใบ</div>
          <div class="seal-kpi-sub">เปิดได้ 50 ซีล / 1 การ์ดเปิดผนึก (หากเปิดทีเดียวครบ ${s.master_seals.toLocaleString()} ใบ ใช้ ${s.master_openers} ใบ)</div>
        </div>
        <div class="seal-kpi">
          <div class="seal-kpi-label"><img src="${esc(closerIcon)}" alt=""> การ์ดปิดผนึก (ถอดคืนทั้งหมด)</div>
          <div class="seal-kpi-val" style="color:#fbbf24">${s.master_closers.toLocaleString()} ใบ</div>
          <div class="seal-kpi-sub">ปิดผนึก 1 ใบ = 50 ซีล · ถอดครบจะได้ซีลการ์ดกลับเข้ากระเป๋า <strong>${s.master_seals.toLocaleString()} ใบ (1:1)</strong></div>
        </div>
        <div class="seal-kpi">
          <div class="seal-kpi-label">ขั้นเริ่มต้น (Normal)</div>
          <div class="seal-kpi-val" style="color:#86efac">${esc(normalTier.stat_display)}</div>
          <div class="seal-kpi-sub">ใช้ซีล <strong>${normalTier.min_seals} ใบ</strong> + การ์ดเปิดผนึก <strong>${normalTier.openers_total_direct} ใบ</strong> ก็ได้บัฟทันที</div>
        </div>
      </div>

      <div class="seal-panel">
        <h3 class="seal-panel-title"><img src="/images/ui/ui_seal.png" class="btn-game-icon" alt=""> ตารางปลดขั้นซีลทั้งหมด 6 ขั้น (สเตตัสที่ได้รับ · การ์ดเปิดผนึก · การ์ดปิดผนึก)</h3>
        <div class="seal-table-wrap">
          <table class="seal-tier-table">
            <thead>
              <tr>
                <th>ระดับ (Rank)</th>
                <th>จำนวนซีลที่ต้องเปิด</th>
                <th>ต้องสะสมเพิ่มจากขั้นก่อน</th>
                <th>ค่าสเตตัส (${esc(s.stat_key)})</th>
                <th>การ์ดเปิดผนึก (รวมตั้งแต่ 0)</th>
                <th>การ์ดปิดผนึก (หากถอดที่ขั้นนี้)</th>
              </tr>
            </thead>
            <tbody>${tierRows}</tbody>
          </table>
        </div>
        <div style="margin-top:10px;font-size:0.78rem;color:var(--text-muted);line-height:1.5">
          * หมายเหตุ: <strong>การ์ดเปิดผนึก 1 ใบ</strong> เปิดใช้งานซีลได้สูงสุด <strong>50 ใบ</strong> (หากเปิดเศษไม่ครบ 50 เช่น เปิดทีละ 1 ใบในขั้น Normal จะถูกหัก 1 ใบทันที) ดังนั้นหากเก็บครบ <strong>${s.master_seals.toLocaleString()}</strong> ใบแล้วกดเปิดรวดเดียว ใช้เพียง <strong>${s.master_openers}</strong> ใบ แต่ถ้าทยอยเปิดแยกครั้งย่อยหลายรอบ อาจใช้การ์ดเปิดผนึกเพิ่มขึ้นตามจำนวนครั้งที่กด
        </div>
      </div>

      <div class="seal-panel">
        <h3 class="seal-panel-title"><img src="/images/client_items/131000.png" class="btn-game-icon" alt=""> เครื่องคำนวณการ์ดเปิดผนึก / การ์ดปิดผนึก</h3>
        <div class="seal-calc-box">
          <div class="seal-calc-controls">
            <label for="seal-calc-qty" style="font-size:0.86rem;font-weight:700">จำนวนซีลที่ต้องการ:</label>
            <input type="number" id="seal-calc-qty" class="seal-calc-input" min="1" max="${s.master_seals}" value="${s.master_seals}" oninput="updateSealCalculator()">
            <div class="seal-calc-presets">${presetBtns}</div>
          </div>
          <div id="seal-calc-output" class="seal-calc-result"></div>
        </div>
      </div>

      <div class="seal-panel">
        <h3 class="panel-title">แหล่งหาซีล (แมพที่ดรอป · NPC แลกเปลี่ยน · การ์ดมอนสเตอร์ / แพ็ก)</h3>
        <div class="seal-sources-grid">
          <div class="seal-src-box">
            <h4>แมพที่ดรอป (${(s.hunting_maps || []).length} แมพ)</h4>
            ${mapsHtml}
          </div>
          <div class="seal-src-box">
            <h4>NPC แลกเปลี่ยน / คราฟต์ (${(s.crafts || []).length} สูตร)</h4>
            ${craftsHtml}
          </div>
          <div class="seal-src-box">
            <h4>การ์ดมอนสเตอร์ / แพ็ก / กิจกรรม</h4>
            ${extraHtml}
          </div>
        </div>
      </div>
    </div>
  `;
  updateSealCalculator();
  initSealLeaderViewer(s);
}

function updateSealCalculator() {
  const s = SEAL_STATE.currentSeal;
  const out = document.getElementById('seal-calc-output');
  const inp = document.getElementById('seal-calc-qty');
  if (!s || !out || !inp) return;
  let qty = parseInt(inp.value, 10);
  if (!Number.isFinite(qty) || qty < 1) qty = 1;
  if (qty > s.master_seals) qty = s.master_seals;

  let activeTier = null;
  for (const t of s.tiers) {
    if (qty >= t.min_seals) activeTier = t;
  }
  const openers = Math.ceil(qty / 50);
  const closers = Math.ceil(qty / 50);

  out.innerHTML = `
    <div>
      <div style="font-size:0.76rem;color:var(--text-muted)">ระดับขั้น &amp; สเตตัสที่ได้ (${qty.toLocaleString()} ซีล)</div>
      <div style="font-size:1.05rem;font-weight:800;color:${activeTier ? esc(activeTier.color) : 'var(--text-main)'};margin-top:3px">
        ${activeTier ? `${esc(activeTier.name_en)} (${esc(activeTier.name_th)}) · ${esc(s.stat_key)} ${esc(activeTier.stat_display)}` : 'ยังไม่ถึงระดับ Normal'}
      </div>
    </div>
    <div>
      <div style="font-size:0.76rem;color:var(--text-muted)">ใช้การ์ดเปิดผนึก (เมื่อเปิดพร้อมกัน)</div>
      <div style="font-size:1.05rem;font-weight:800;color:#38bdf8;margin-top:3px">${openers.toLocaleString()} ใบ</div>
      <div style="font-size:0.74rem;color:var(--text-sub)">ปัดขึ้น(${qty.toLocaleString()} ÷ 50)</div>
    </div>
    <div>
      <div style="font-size:0.76rem;color:var(--text-muted)">หากใช้การ์ดปิดผนึกถอดซีล ${qty.toLocaleString()} ใบ</div>
      <div style="font-size:1.05rem;font-weight:800;color:#fbbf24;margin-top:3px">ใช้ ${closers.toLocaleString()} ใบ → ได้ซีลกลับ ${qty.toLocaleString()} ใบ</div>
      <div style="font-size:0.74rem;color:var(--text-sub)">ได้ซีลกลับคืนเข้ากระเป๋า 1:1 แลกเปลี่ยนได้</div>
    </div>
  `;
}

// ==========================================
// 3D SEAL MASTER LEADER PREVIEW (ข้างหัวเทมเมอร์)
// ==========================================
let SEAL_LEADER_TAMERS = null;
let ACTIVE_SEAL_LEADER_VIEWER = null;

function disposeSealLeaderSceneObject(root) {
  if (!root || !root.traverse) return;
  root.traverse(obj => {
    if (obj.geometry && typeof obj.geometry.dispose === 'function') {
      obj.geometry.dispose();
    }
    if (obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      mats.forEach(mat => {
        if (!mat) return;
        ['map', 'alphaMap', 'emissiveMap', 'normalMap', 'roughnessMap', 'metalnessMap'].forEach(k => {
          if (mat[k] && typeof mat[k].dispose === 'function') mat[k].dispose();
        });
        if (typeof mat.dispose === 'function') mat.dispose();
      });
    }
  });
}

function disposeSealLeaderViewer() {
  if (!ACTIVE_SEAL_LEADER_VIEWER) return;
  const st = ACTIVE_SEAL_LEADER_VIEWER;
  ACTIVE_SEAL_LEADER_VIEWER = null;
  try {
    if (st.raf) cancelAnimationFrame(st.raf);
    if (st.onResize) window.removeEventListener('resize', st.onResize);
    if (st.tamerGroup) disposeSealLeaderSceneObject(st.tamerGroup);
    if (st.leaderGroup) disposeSealLeaderSceneObject(st.leaderGroup);
    if (st.controls) st.controls.dispose();
    if (st.envRT) st.envRT.dispose();
    if (st.renderer) {
      st.renderer.dispose();
      st.renderer.domElement?.remove();
    }
  } catch (e) { }
}

async function getSealLeaderTamers() {
  if (Array.isArray(SEAL_LEADER_TAMERS) && SEAL_LEADER_TAMERS.length) {
    return SEAL_LEADER_TAMERS;
  }
  try {
    const res = await fetch('/api/tamers');
    if (!res.ok) return [];
    const data = await res.json();
    const list = (data.items || []).filter(t => t && t.model_url);
    SEAL_LEADER_TAMERS = list;
    return list;
  } catch (e) {
    return [];
  }
}

function setSealLeaderCameraPreset(preset) {
  const st = ACTIVE_SEAL_LEADER_VIEWER;
  if (!st) return;
  st.camPreset = preset === 'body' ? 'body' : 'head';
  const btnHead = document.getElementById('seal-leader-cam-head');
  const btnBody = document.getElementById('seal-leader-cam-body');
  if (btnHead) btnHead.classList.toggle('active', st.camPreset === 'head');
  if (btnBody) btnBody.classList.toggle('active', st.camPreset === 'body');

  const H = st.tamerHeight || 150;
  const ax = st.anchorX || -H * 0.25;
  if (st.camPreset === 'body') {
    st.homeTarget.set(ax * 0.34, H * 0.50, 0);
    st.homeCamPos.set(H * 0.06, H * 0.56, H * 1.92);
  } else {
    st.homeTarget.set(ax * 0.42, H * 0.90, 0);
    st.homeCamPos.set(ax * 0.20, H * 0.94, H * 0.74);
  }
  st.camera.position.copy(st.homeCamPos);
  st.controls.target.copy(st.homeTarget);
  st.controls.update();
}

function toggleSealLeaderAutoRotate() {
  const st = ACTIVE_SEAL_LEADER_VIEWER;
  if (!st) return;
  st.controls.autoRotate = !st.controls.autoRotate;
  const btn = document.getElementById('seal-leader-btn-rot');
  if (btn) btn.classList.toggle('active', st.controls.autoRotate);
}

function resetSealLeaderCamera() {
  const st = ACTIVE_SEAL_LEADER_VIEWER;
  if (!st) return;
  setSealLeaderCameraPreset(st.camPreset || 'head');
}

function _buildSealLeaderCardMesh(seal, H) {
  const group = new THREE.Group();
  const cardW = H * 0.145;
  const cardH = H * 0.185;
  const cardD = Math.max(H * 0.012, 1.4);

  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x6b21a8,
    emissive: 0x3b0764,
    emissiveIntensity: 0.45,
    metalness: 0.68,
    roughness: 0.26,
  });
  const frameGeo = new THREE.BoxGeometry(cardW + cardD * 1.4, cardH + cardD * 1.4, cardD);
  const frameMesh = new THREE.Mesh(frameGeo, frameMat);
  group.add(frameMesh);

  const trimMat = new THREE.MeshStandardMaterial({
    color: 0xfbbf24,
    emissive: 0x78350f,
    emissiveIntensity: 0.35,
    metalness: 0.82,
    roughness: 0.22,
  });
  const trimGeo = new THREE.BoxGeometry(cardW + cardD * 1.85, cardH + cardD * 1.85, cardD * 0.48);
  const trimMesh = new THREE.Mesh(trimGeo, trimMat);
  group.add(trimMesh);

  const innerBackMat = new THREE.MeshStandardMaterial({
    color: 0x0f172a,
    emissive: 0x1e1b4b,
    emissiveIntensity: 0.35,
    roughness: 0.4,
    metalness: 0.25,
  });
  const innerBackMesh = new THREE.Mesh(new THREE.BoxGeometry(cardW, cardH, cardD * 1.01), innerBackMat);
  group.add(innerBackMesh);

  const artUrl = seal.image || '/images/Seal_Icon.png';
  const texLoader = new THREE.TextureLoader();
  const artTex = texLoader.load(artUrl, undefined, undefined, () => {
    texLoader.load('/images/Seal_Icon.png');
  });
  artTex.encoding = THREE.sRGBEncoding;

  const faceGeo = new THREE.PlaneGeometry(cardW * 0.94, cardH * 0.94);
  const faceMat = new THREE.MeshStandardMaterial({
    map: artTex,
    transparent: true,
    alphaTest: 0.04,
    roughness: 0.35,
    metalness: 0.10,
  });
  const frontFace = new THREE.Mesh(faceGeo, faceMat);
  frontFace.position.z = cardD * 0.53;
  group.add(frontFace);

  const backFace = new THREE.Mesh(faceGeo.clone(), faceMat.clone());
  backFace.rotation.y = Math.PI;
  backFace.position.z = -cardD * 0.53;
  group.add(backFace);

  return group;
}

function _clearGroupChildren(group) {
  if (!group) return;
  while (group.children.length) {
    const ch = group.children[group.children.length - 1];
    group.remove(ch);
    disposeSealLeaderSceneObject(ch);
  }
}

function _loadSealLeaderActorInto(st) {
  const seal = st.seal;
  if (!st.leaderPivot) return;
  _clearGroupChildren(st.leaderPivot);
  st.leaderHalo = null;
  const H = st.tamerHeight || 150;
  const useDigimon3D = st.mode === 'digimon_3d' && !!seal.leader_model_url;

  const badgeEl = document.getElementById('seal-leader-mode-badge');
  const isDatsAgumon = seal.mon_id === 31000 && useDigimon3D;
  if (badgeEl) {
    badgeEl.textContent = useDigimon3D
      ? (isDatsAgumon ? 'Master Leader (อากูมอน S · ประจำตรา DATS)' : 'Master Leader (โมเดล 3D ข้างหัวเทมเมอร์)')
      : 'Master Hologram (การ์ด 3D ข้างหัวเทมเมอร์)';
  }

  const attachVisual = (node, heightEstimate, isCard) => {
    if (ACTIVE_SEAL_LEADER_VIEWER !== st) {
      disposeSealLeaderSceneObject(node);
      return;
    }
    _clearGroupChildren(st.leaderPivot);
    st.leaderPivot.add(node);
    st.isCardMode = !!isCard;

    const halo = _buildMagicHaloGroup(heightEstimate * 0.34, 0xc084fc, true);
    halo.position.y = -heightEstimate * 0.56;
    st.leaderPivot.add(halo);
    st.leaderHalo = halo;
  };

  if (!useDigimon3D) {
    const cardMesh = _buildSealLeaderCardMesh(seal, H);
    attachVisual(cardMesh, H * 0.185, true);
    return;
  }

  const loader = new THREE.GLTFLoader();
  loader.load(
    seal.leader_model_url,
    gltf => {
      if (ACTIVE_SEAL_LEADER_VIEWER !== st) return;
      const raw = gltf.scene;
      _enhanceStudioGLTFModel(raw, st.renderer, { envIntensity: 0.48 });
      const box = new THREE.Box3().setFromObject(raw);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z, 0.01);
      const targetDim = H * 0.19;
      const scale = targetDim / maxDim;

      const wrap = new THREE.Group();
      raw.scale.setScalar(scale);
      raw.position.set(-center.x * scale, -center.y * scale, -center.z * scale);
      wrap.rotation.y = 0.26;
      wrap.add(raw);
      attachVisual(wrap, Math.max(size.y * scale, H * 0.22), false);
    },
    undefined,
    () => {
      if (ACTIVE_SEAL_LEADER_VIEWER !== st) return;
      const fallbackCard = _buildSealLeaderCardMesh(seal, H);
      attachVisual(fallbackCard, H * 0.185, true);
    }
  );
}

function setSealLeaderMode(mode) {
  const st = ACTIVE_SEAL_LEADER_VIEWER;
  if (!st) return;
  st.mode = mode === 'digimon_3d' && st.seal?.leader_model_url ? 'digimon_3d' : 'card_3d';
  const b3d = document.getElementById('seal-leader-mode-3d');
  const bcard = document.getElementById('seal-leader-mode-card');
  if (b3d) b3d.classList.toggle('active', st.mode === 'digimon_3d');
  if (bcard) bcard.classList.toggle('active', st.mode === 'card_3d');
  _loadSealLeaderActorInto(st);
}

function changeSealLeaderTamer(tamerId) {
  const st = ACTIVE_SEAL_LEADER_VIEWER;
  if (!st || !tamerId) return;
  SEAL_STATE.previewTamerId = String(tamerId);
  _loadSealLeaderTamerInto(st, String(tamerId));
}

function _loadSealLeaderTamerInto(st, tamerId) {
  const tamers = st.tamers || [];
  const tamer = tamers.find(t => String(t.id) === String(tamerId)) || tamers[0];
  const statusEl = document.getElementById('seal-leader-status');
  if (!tamer || !tamer.model_url) {
    if (statusEl) statusEl.textContent = 'ไม่พบโมเดล 3D ของเทมเมอร์';
    return;
  }
  if (statusEl) {
    statusEl.style.display = 'flex';
    statusEl.textContent = `กำลังโหลด ${tamer.name_th} + Master Leader...`;
  }

  _clearGroupChildren(st.tamerGroup);

  const loader = new THREE.GLTFLoader();
  loader.load(
    tamer.model_url,
    gltf => {
      if (ACTIVE_SEAL_LEADER_VIEWER !== st) return;
      const root = gltf.scene;
      _enhanceStudioGLTFModel(root, st.renderer, { envIntensity: 0.42 });
      const box = new THREE.Box3().setFromObject(root);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const H = Math.max(size.y, 10);

      root.position.set(-center.x, -box.min.y, -center.z);
      st.tamerGroup.add(root);

      const floorHalo = _buildMagicHaloGroup(H * 0.19, 0x38bdf8, false);
      floorHalo.position.set(0, 0.4, 0);
      st.tamerGroup.add(floorHalo);

      st.tamerHeight = H;
      st.anchorX = -H * 0.25;
      st.anchorY = H * 0.96;
      st.anchorZ = H * 0.05;
      st.leaderGroup.position.set(st.anchorX, st.anchorY, st.anchorZ);

      _loadSealLeaderActorInto(st);
      setSealLeaderCameraPreset(st.camPreset || 'head');
      if (statusEl) statusEl.style.display = 'none';
    },
    undefined,
    () => {
      if (statusEl) statusEl.textContent = 'โหลดโมเดลเทมเมอร์ไม่สำเร็จ';
    }
  );
}

async function initSealLeaderViewer(seal) {
  disposeSealLeaderViewer();
  const host = document.getElementById('seal-leader-viewer');
  if (!host || !seal) return;

  const hasModel = !!seal.leader_model_url;
  const initMode = hasModel ? 'digimon_3d' : 'card_3d';
  const tamers = await getSealLeaderTamers();
  if (!document.getElementById('seal-leader-viewer') || SEAL_STATE.currentSeal?.id !== seal.id) return;

  const defaultTid = SEAL_STATE.previewTamerId && tamers.some(t => String(t.id) === String(SEAL_STATE.previewTamerId))
    ? String(SEAL_STATE.previewTamerId)
    : (tamers.find(t => String(t.id) === '80001')?.id ? '80001' : String(tamers[0]?.id || ''));

  const tamerOptions = tamers.map(t =>
    `<option value="${esc(String(t.id))}" ${String(t.id) === defaultTid ? 'selected' : ''}>${esc(t.name_th)}${t.series ? ` (${esc(t.series)})` : ''}</option>`
  ).join('');

  host.innerHTML = `
    <div class="seal-leader-toolbar">
      <div style="display:flex;flex-direction:column;gap:2px">
        <h3 class="seal-panel-title" style="margin:0"><img src="/images/ui/ui_seal.png" class="btn-game-icon" alt=""> ตัวอย่างระบบ Seal Master — ยืน/ลอยข้างหัวเทมเมอร์ (3D)</h3>
        <span style="font-size:0.78rem;color:var(--text-muted)">เมื่อสะสม ${esc(seal.name_th)} ครบ <strong>${seal.master_seals.toLocaleString()}</strong> ใบ และตั้งเป็น Leader จะปรากฏข้างหัวเทมเมอร์แบบเรียลไทม์</span>
      </div>
      <div class="seal-leader-controls">
        ${tamers.length ? `
          <label for="seal-leader-tamer-sel" style="font-size:0.76rem;color:var(--text-muted)">เทมเมอร์:</label>
          <select id="seal-leader-tamer-sel" class="seal-tamer-select" onchange="changeSealLeaderTamer(this.value)">${tamerOptions}</select>
        ` : ''}
        ${hasModel ? `
          <button id="seal-leader-mode-3d" class="filter-pill active" type="button" onclick="setSealLeaderMode('digimon_3d')">โมเดล 3D</button>
          <button id="seal-leader-mode-card" class="filter-pill" type="button" onclick="setSealLeaderMode('card_3d')">การ์ดซีล 3D</button>
        ` : ''}
        <button id="seal-leader-cam-head" class="filter-pill active" type="button" onclick="setSealLeaderCameraPreset('head')">ข้างหัวเทมเมอร์</button>
        <button id="seal-leader-cam-body" class="filter-pill" type="button" onclick="setSealLeaderCameraPreset('body')">มุมเต็มตัว</button>
        <button id="seal-leader-btn-rot" class="filter-pill" type="button" onclick="toggleSealLeaderAutoRotate()">หมุน 360°</button>
      </div>
    </div>
    <div id="seal-leader-stage" class="seal-leader-stage">
      <div id="seal-leader-mode-badge" class="seal-leader-badge-overlay">${hasModel ? (seal.mon_id === 31000 ? 'Master Leader (อากูมอน S · ประจำตรา DATS)' : 'Master Leader (โมเดล 3D ข้างหัวเทมเมอร์)') : 'Master Hologram (การ์ด 3D ข้างหัวเทมเมอร์)'}</div>
      <div id="seal-leader-status" class="seal-leader-status">กำลังเตรียมฉาก 3D...</div>
      <div class="seal-leader-hint">ลากเพื่อหมุนมุมมอง 360° · เลื่อนเมาส์เพื่อซูมเข้า-ออก · คลิกขวาเพื่อเลื่อนตำแหน่ง</div>
    </div>
    <div class="seal-leader-note">
      <span>รูปแบบ Leader: <strong>${hasModel ? (seal.mon_id === 31000 ? 'อากูมอน (S) — โมเดลประจำตรา DATS (สลับดูการ์ด 3D ได้)' : 'โมเดล 3D จริงจาก Client (สลับดูการ์ด 3D ได้)') : 'การ์ดโฮโลแกรม Master 3D (สำหรับซีลกิจกรรม/สัญลักษณ์)'}</strong></span>
    </div>
  `;

  const stage = document.getElementById('seal-leader-stage');
  const statusEl = document.getElementById('seal-leader-status');
  if (!stage || typeof THREE === 'undefined' || !THREE.GLTFLoader) {
    if (statusEl) statusEl.textContent = 'เบราว์เซอร์ไม่รองรับตัวแสดงผล 3D (Three.js)';
    return;
  }

  const { scene, camera, renderer, envRT } = _createStudioStageRig(stage, {
    defaultW: 640,
    defaultH: 490,
    fov: 34,
    rimColor: 0xa78bfa,
    shadowRadius: 150,
  });

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = false;
  controls.autoRotateSpeed = 1.6;

  const tamerGroup = new THREE.Group();
  const leaderGroup = new THREE.Group();
  const leaderPivot = new THREE.Group();
  leaderGroup.add(leaderPivot);
  scene.add(tamerGroup);
  scene.add(leaderGroup);

  const st = {
    seal,
    tamers,
    mode: initMode,
    camPreset: 'head',
    scene,
    camera,
    renderer,
    envRT,
    controls,
    tamerGroup,
    leaderGroup,
    leaderPivot,
    leaderHalo: null,
    isCardMode: !hasModel,
    tamerHeight: 150,
    anchorX: -40,
    anchorY: 135,
    anchorZ: 10,
    homeCamPos: new THREE.Vector3(-12, 135, 145),
    homeTarget: new THREE.Vector3(-18, 128, 0),
    raf: 0,
    onResize: null,
  };
  ACTIVE_SEAL_LEADER_VIEWER = st;

  st.onResize = () => {
    if (!stage.isConnected) return;
    const w = stage.clientWidth || 640;
    const h = stage.clientHeight || 490;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener('resize', st.onResize);

  _loadSealLeaderTamerInto(st, defaultTid);

  const t0 = performance.now();
  const animate = () => {
    if (ACTIVE_SEAL_LEADER_VIEWER !== st) return;
    st.raf = requestAnimationFrame(animate);
    const t = (performance.now() - t0) * 0.001;
    const bobAmp = (st.tamerHeight || 150) * 0.016;
    st.leaderPivot.position.y = Math.sin(t * 2.2) * bobAmp;
    if (st.isCardMode) {
      st.leaderPivot.rotation.y = Math.sin(t * 1.15) * 0.28;
    } else {
      st.leaderPivot.rotation.y = Math.sin(t * 0.9) * 0.10;
    }
    if (st.leaderHalo) {
      st.leaderHalo.rotation.y = t * 0.8;
    }
    controls.update();
    renderer.render(scene, camera);
  };
  animate();
}

// ==========================================
// D-UNIT (DIGIMON UNIT / UNION SYSTEM)
// ==========================================
const DUNIT_STATE = {
  data: null,
  activeFilterIds: new Set(),
  activeTab: 'basic', // 'basic' | 'scd_attr' | 'scd_elem'
  rank: 'all',
  selectedGroup: null,
  selectedTitle: null,
};

const DUNIT_TIER_META = {
  1: { badge: 'บรอนซ์', color: '#cd7f32', bg: 'rgba(205,127,50,0.12)', border: 'rgba(205,127,50,0.45)' },
  2: { badge: 'ซิลเวอร์', color: '#c0c0c0', bg: 'rgba(192,192,192,0.12)', border: 'rgba(192,192,192,0.45)' },
  3: { badge: 'โกลด์', color: '#ffd700', bg: 'rgba(255,215,0,0.12)', border: 'rgba(255,215,0,0.45)' },
  4: { badge: 'แพลตตินัม', color: '#00e5ff', bg: 'rgba(0,229,255,0.12)', border: 'rgba(0,229,255,0.45)' },
  5: { badge: 'ไดมอนด์', color: '#c084fc', bg: 'rgba(192,132,252,0.12)', border: 'rgba(192,132,252,0.45)' },
  6: { badge: 'มาสเตอร์', color: '#ff3366', bg: 'rgba(255,51,102,0.15)', border: 'rgba(255,51,102,0.5)' }
};

const DUNIT_KIT_RANKS = ['all', 'N', 'A', 'A+', 'S', 'S+', 'SS', 'SS+', 'SSS'];

async function loadDUnits() {
  if (!DUNIT_STATE.data) {
    const grid = document.getElementById('dunit-grid');
    if (grid) grid.innerHTML = '<div class="empty-note">กำลังโหลดข้อมูล D-ยูนิตจากเซิร์ฟไทย...</div>';
    try {
      const res = await fetch('/api/dunits');
      DUNIT_STATE.data = await res.json();
    } catch (e) {
      console.error('Failed to load D-Units:', e);
      if (grid) grid.innerHTML = '<div class="empty-note error">โหลดข้อมูล D-ยูนิตไม่สำเร็จ</div>';
      return;
    }
  }

  renderDUnitTiers();
  renderDUnitFilters();
  renderDUnits();
}

function renderDUnitTiers() {
  const container = document.getElementById('dunit-tiers-row');
  if (!container || !DUNIT_STATE.data) return;
  const tiers = DUNIT_STATE.data.master_tiers || [];

  container.innerHTML = tiers.map(t => {
    const meta = DUNIT_TIER_META[t.tier_id] || { badge: t.tier_name, color: 'var(--color-primary)', bg: 'var(--card-bg)', border: 'var(--border-color)' };
    return `
      <div class="dunit-tier-card" style="border-color:${meta.border}; background: ${meta.bg}" onclick="openDUnitTitleModal(${t.tier_id})" title="คลิกดูรายละเอียดและบัฟฉายา">
        <div class="dunit-tier-badge" style="color:${meta.color}">${meta.badge}</div>
        <div class="dunit-tier-req">ปลดล็อก <strong>${t.req_units}</strong> กลุ่ม</div>
        <div class="dunit-tier-reward" title="${esc(t.title_reward)}">
          <span class="dunit-reward-tag">ฉายา</span>
          <span class="dunit-reward-text">${esc(t.title_reward || '-')}</span>
        </div>
        ${t.buffs ? `<div style="font-size:0.7rem;color:#38bdf8;margin-top:2px;font-weight:600">${esc(t.buffs)}</div>` : ''}
      </div>
    `;
  }).join('');
}

function openDUnitTitleModal(tierId) {
  if (!DUNIT_STATE.data) return;
  const tiers = DUNIT_STATE.data.master_tiers || [];
  const tier = tiers.find(t => t.tier_id === tierId);
  if (!tier) return;

  const modal = document.getElementById('dunit-title-modal');
  if (!modal) return;

  const meta = DUNIT_TIER_META[tier.tier_id] || { color: '#ffd700' };
  const statChips = (tier.stats || []).map(s => `<span class="dunit-title-buff-chip">${esc(s.stat)} <strong>${esc(s.val)}</strong></span>`).join('');

  modal.innerHTML = `
    <div class="dunit-modal-box" style="max-width:540px" onclick="event.stopPropagation()">
      <div class="dunit-modal-header">
        <div class="dunit-modal-title">
          <img src="/images/ui/ui_ach.png" style="width:26px;height:26px;object-fit:contain" alt="">
          <h2>ฉายา D-ยูนิต ${esc(tier.tier_name)}</h2>
        </div>
        <button class="dunit-modal-close" onclick="closeDUnitTitleModal()">&times;</button>
      </div>
      <div class="dunit-modal-body">
        <div class="dunit-title-card">
          <img class="dunit-title-icon" src="${esc(tier.reward_item_icon)}" alt="" onerror="this.src='/images/Icon_-_Title.png'">
          <div class="dunit-title-meta">
            <div class="dunit-title-name" style="color:${meta.color}">${esc(tier.title_reward)}</div>
            <div class="dunit-title-req">เงื่อนไข: ปลดล็อก D-ยูนิต ครบ <strong>${tier.req_units}</strong> กลุ่ม</div>
          </div>
        </div>

        <div class="dunit-title-buffs-box">
          <div class="dunit-title-buffs-header"><img src="/images/AT.png" class="stat-icon-inline" alt=""> ผลบัฟเมื่อสวมใส่ฉายานี้ (Title Buffs)</div>
          <div class="dunit-title-buffs-list">
            ${statChips || `<span class="dunit-title-buff-chip">${esc(tier.buffs || 'ไม่มีข้อมูล')}</span>`}
          </div>
        </div>

        ${tier.desc ? `<div class="dunit-title-desc"><strong>คำอธิบายในเกม:</strong> ${esc(tier.desc)}</div>` : ''}
      </div>
    </div>
  `;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeDUnitTitleModal() {
  const modal = document.getElementById('dunit-title-modal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = '';
}

function renderDUnitFilters() {
  const tabsBox = document.getElementById('dunit-filter-tabs');
  const checksGrid = document.getElementById('dunit-checkbox-grid');
  const actionsBox = document.getElementById('dunit-filter-actions');
  const rankBox = document.getElementById('dunit-rank-pills');
  if (!tabsBox || !checksGrid || !DUNIT_STATE.data) return;

  const sections = DUNIT_STATE.data.filter_sections || [];
  const curSec = sections.find(s => s.id === DUNIT_STATE.activeTab) || sections[0];

  // Render Tabs
  tabsBox.innerHTML = sections.map(s => {
    const isAct = s.id === DUNIT_STATE.activeTab;
    const actCount = (s.filters || []).filter(f => DUNIT_STATE.activeFilterIds.has(f.id)).length;
    const badge = actCount ? ` <span class="dunit-pill-total" style="background:#0284c7;color:#fff">${actCount}</span>` : '';
    return `
      <button class="dunit-ftab-btn${isAct ? ' active' : ''}" type="button" onclick="setDUnitFilterTab('${s.id}')">
        <span>${esc(s.title)}</span>${badge}
      </button>
    `;
  }).join('');

  // Render Checkboxes under active tab (Images 3, 4, 5 style)
  if (curSec) {
    checksGrid.innerHTML = (curSec.filters || []).map(f => {
      const isChecked = DUNIT_STATE.activeFilterIds.has(f.id);
      return `
        <div class="dunit-check-item${isChecked ? ' active' : ''}" onclick="toggleDUnitFilter(${f.id})">
          <div class="dunit-custom-box">
            <svg viewBox="0 0 24 24" fill="none"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
          <span>${esc(f.name)}</span>
          <span class="dunit-check-count">(${f.count})</span>
        </div>
      `;
    }).join('');
  }

  // Render Actions row
  const totalActive = DUNIT_STATE.activeFilterIds.size;
  if (actionsBox) {
    actionsBox.innerHTML = `
      <div style="color:var(--text-muted)">
        ${totalActive ? `เลือกอยู่: <strong style="color:#38bdf8">${totalActive}</strong> ตัวกรอง` : 'เลือกสเตตัสที่ต้องการกรองบัฟ (เลือกได้หลายช่อง)'}
      </div>
      ${totalActive || DUNIT_STATE.rank !== 'all' ? `
        <button class="dunit-clear-btn" type="button" onclick="clearAllDUnitFilters()">ล้างตัวกรองทั้งหมด</button>
      ` : ''}
    `;
  }

  // Render Rank Pills
  if (rankBox) {
    rankBox.innerHTML = DUNIT_KIT_RANKS.map(r => {
      const isAct = DUNIT_STATE.rank === r;
      const label = r === 'all' ? 'ทุกระดับคิท' : `ระดับ ${r}`;
      return `<button class="filter-pill${isAct ? ' active' : ''}" type="button" onclick="setDUnitRankFilter('${esc(r)}')">
        ${label}
      </button>`;
    }).join('');
  }
}

function setDUnitFilterTab(tabId) {
  DUNIT_STATE.activeTab = tabId;
  renderDUnitFilters();
}

function toggleDUnitFilter(fid) {
  if (DUNIT_STATE.activeFilterIds.has(fid)) {
    DUNIT_STATE.activeFilterIds.delete(fid);
  } else {
    DUNIT_STATE.activeFilterIds.add(fid);
  }
  renderDUnitFilters();
  renderDUnits();
}

function setDUnitRankFilter(rank) {
  DUNIT_STATE.rank = rank;
  renderDUnitFilters();
  renderDUnits();
}

function clearAllDUnitFilters() {
  DUNIT_STATE.activeFilterIds.clear();
  DUNIT_STATE.rank = 'all';
  const inp = document.getElementById('dunit-search-input');
  if (inp) inp.value = '';
  renderDUnitFilters();
  renderDUnits();
}

function renderDUnits() {
  const grid = document.getElementById('dunit-grid');
  const summaryBox = document.getElementById('dunit-summary-bar');
  if (!grid || !DUNIT_STATE.data) return;

  const q = (document.getElementById('dunit-search-input')?.value || '').trim().toLowerCase();
  const groups = DUNIT_STATE.data.groups || [];

  const filtered = groups.filter(g => {
    // Multi-select Checkbox Filter
    if (DUNIT_STATE.activeFilterIds.size > 0) {
      const gFids = new Set(g.filter_ids || []);
      let hasMatch = false;
      for (const fid of DUNIT_STATE.activeFilterIds) {
        if (gFids.has(fid)) {
          hasMatch = true;
          break;
        }
      }
      if (!hasMatch) return false;
    }

    // Rank filter
    if (DUNIT_STATE.rank !== 'all') {
      const hasRank = (g.members || []).some(m => m.rank === DUNIT_STATE.rank || (m.hacking && m.hacking.kit_name.includes(` ${DUNIT_STATE.rank}`)));
      if (!hasRank) return false;
    }

    // Search query
    if (q) {
      const hay = [
        g.name,
        String(g.id),
        (g.tiers || []).map(t => `${t.cond_desc} ${t.buff_text}`).join(' '),
        ...(g.members || []).map(m => `${m.name} ${m.title} ${m.base_name} ${m.rank}`)
      ].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }

    return true;
  });

  if (summaryBox) {
    summaryBox.innerHTML = `
      <div class="dunit-sum-content">
        <span>พบ <strong>${filtered.length}</strong> จากทั้งหมด ${groups.length} กลุ่ม D-ยูนิต (คลิกการ์ดเพื่อดูการ์ด 8 ใบและผลของการสะสม)</span>
        <span class="dunit-sum-note">เงื่อนไขการแฮก: ดิจิมอน Lv.31+ และใช้ D-ยูนิตแฮกกิ้งคิท 100 ชิ้น</span>
      </div>
    `;
  }

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-note">ไม่พบกลุ่ม D-ยูนิต ที่ตรงกับเงื่อนไขการค้นหา</div>';
    return;
  }

  grid.innerHTML = filtered.map(g => {
    // 4 Collection Tiers snippet
    const tiersHtml = (g.tiers || []).map(t => `
      <div class="dunit-tier-row">
        <span class="dunit-t-step${t.tier > 2 ? ' tier-2' : ''}">ขั้น ${t.tier}</span>
        <span class="dunit-t-req">${esc(t.cond_desc)}</span>
        <span class="dunit-t-desc">${esc(t.buff_text)}</span>
      </div>
    `).join('');

    // Mini card avatars row: only real members, no empty dashed circle slots
    const miniCards = (g.cards || []).filter(c => !c.is_empty).slice(0, 8).map(c => `
      <div style="position:relative;width:28px;height:28px;border-radius:50%;border:1.5px solid #ef4444;background:#000;overflow:hidden;display:inline-block;box-shadow:0 0 5px rgba(239,68,68,0.5)" title="${esc(c.name)} (${esc(c.rank)})">
        <img src="${esc(c.icon || PLACEHOLDER)}" alt="" style="width:100%;height:100%;object-fit:cover" onerror="this.src='${PLACEHOLDER}'">
      </div>
    `).join('');

    return `
      <div class="dunit-group-card" id="dunit-${g.id}" onclick="openDUnitGroupModal(${g.id})">
        <div class="dunit-group-header">
          <div class="dunit-gh-left">
            <h3 class="dunit-group-title">${esc(g.name)}</h3>
          </div>
        </div>

        <div class="dunit-tiers-box">
          <div class="dunit-tiers-header"><img src="/images/ui/ui_dunit.png" class="stat-icon-inline" alt=""> ผลของการสะสม (Collection Effects)</div>
          ${tiersHtml}
        </div>

        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:2px">
          <div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap">${miniCards}</div>
          <span style="font-size:0.75rem;color:var(--text-muted);font-weight:700">${g.member_count} ตัว</span>
        </div>

        <div class="dunit-click-hint">
          <span>คลิกเพื่อดูการ์ดสมาชิก & ผลของการสะสมทั้งหมด</span>
        </div>
      </div>
    `;
  }).join('');
}

function openDUnitGroupModal(groupId) {
  if (!DUNIT_STATE.data) return;
  const groups = DUNIT_STATE.data.groups || [];
  const g = groups.find(x => x.id === groupId);
  if (!g) return;

  const modal = document.getElementById('dunit-group-modal');
  if (!modal) return;

  // Max level in Thai server patch is Lv. 180 (members * 180, e.g. 11 * 180 = 1980 in Mode group)
  const maxLevel = g.max_cum_level || (g.member_count * 180) || 1440;
  const curLevel = maxLevel;

  // 1. "ผลของการสะสม" HUD (Image 1 Style): แสดงผ่าน สีเหลืองเรืองแสงครบทุกขั้น
  const hudTiersHtml = (g.tiers || []).map(t => `
    <div class="dunit-hud-tier-row active">
      <span>${esc(t.cond_desc)} , ${esc(t.buff_text)}</span>
    </div>
  `).join('');

  // 2. Member Cards Grid: แสดงสมาชิกจริงทั้งหมด ไม่ fix 8 ใบ และไม่มีช่องว่าง
  const cardsHtml = (g.cards || []).filter(c => !c.is_empty).map(c => {
    const inner = `
      <div class="dunit-card-avatar-ring">
        <img src="${esc(c.icon || PLACEHOLDER)}" alt="${esc(c.name)}" loading="lazy" onerror="this.src='${PLACEHOLDER}'">
      </div>
      <div class="dunit-card-lv">Lv. ${c.max_level || 180}</div>
      <div class="dunit-card-rank-diamond rank-${esc(c.rank || 'N')}">${esc(c.rank || 'N')}</div>
      <div class="dunit-card-name" title="${esc(c.name)}">${esc(c.name)}</div>
    `;
    return c.slug ? `
      <a class="dunit-card-frame" href="${digiHref(c.slug)}" title="คลิกดูข้อมูล ${esc(c.name)} (จาก ${esc(c.base_name)})">
        ${inner}
      </a>
    ` : `
      <div class="dunit-card-frame">
        ${inner}
      </div>
    `;
  }).join('');

  // 3. Hacking Kits Section
  const hackKitsHtml = (g.members || []).filter(m => m.hacking).map(m => `
    <div class="dunit-hack-pill">
      <img class="dunit-hack-icon" src="${esc(m.hacking.kit_icon)}" alt="" onerror="this.src='/images/client_items/75832.png'">
      <div class="dunit-hack-info">
        <div class="dunit-hack-name">${esc(m.name)}</div>
        <div class="dunit-hack-cond">${esc(m.hacking.kit_name)} ×${m.hacking.needed} · Lv.${m.hacking.min_level}+</div>
      </div>
    </div>
  `).join('');

  modal.innerHTML = `
    <div class="dunit-modal-box" onclick="event.stopPropagation()">
      <div class="dunit-modal-header">
        <div class="dunit-modal-title">
          <img src="/images/ui/ui_dunit.png" style="width:26px;height:26px;object-fit:contain" alt="">
          <h2>D-ยูนิต: ${esc(g.name)}</h2>
        </div>
        <button class="dunit-modal-close" onclick="closeDUnitGroupModal()">&times;</button>
      </div>

      <div class="dunit-modal-body">
        <!-- ผลของการสะสม HUD (Image 1 Style) -->
        <div class="dunit-hud-box">
          <div class="dunit-hud-header">
            <div class="dunit-hud-tab">ผลของการสะสม</div>
            <div class="dunit-hud-progress">${curLevel} / ${maxLevel}</div>
          </div>
          <div class="dunit-hud-tiers">
            ${hudTiersHtml}
          </div>
        </div>

        <!-- Cards Grid (แสดงทุกตัว ไม่จำกัด 8) -->
        <div class="dunit-cards-container">
          <div class="dunit-cards-header">
            <span>สมาชิกในยูนิต (${g.member_count} ตัว) · คลิกการ์ดเพื่อดูรายละเอียดดิจิมอน</span>
            <span>ระดับการวิวัฒนาการตาม Client</span>
          </div>
          <div class="dunit-cards-grid">
            ${cardsHtml}
          </div>
        </div>

        <!-- Hacking Requirements -->
        ${hackKitsHtml ? `
        <div class="dunit-hack-section">
          <div class="dunit-hack-title"><img src="/images/ui/ui_dunit.png" class="stat-icon-inline" alt=""> เงื่อนไขแฮกกิ้งคิทประจำตัว (Hacking Kits Required)</div>
          <div class="dunit-hack-grid">
            ${hackKitsHtml}
          </div>
        </div>` : ''}
      </div>
    </div>
  `;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeDUnitGroupModal() {
  const modal = document.getElementById('dunit-group-modal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = '';
}
