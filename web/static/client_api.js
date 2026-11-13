// client_api.js - 100% In-Memory Serverless Data Engine for DMO Thai Wiki
// Intercepts /api/* requests and serves data directly from high-speed static CDN JSON
(function () {
  'use strict';

  const CACHE = {
    digimon: null,
    digimonBySlug: new Map(),
    filters: null,
    rankTable: null,
    dungeons: null,
    tamers: null,
    seals: null,
    decks: null,
    eggs: null,
    jogress: null,
    dunits: null,
    npcExchanges: null,
    patches: null,
    stats: null
  };

  const originalFetch = window.fetch;

  async function loadData(key, path) {
    if (CACHE[key]) return CACHE[key];
    try {
      const res = await originalFetch(path);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      CACHE[key] = data;
      return data;
    } catch (err) {
      console.warn(`[CLIENT_API] Failed to load ${path}, trying R2 fallback...`, err);
      try {
        const r2Path = `https://pub-f7d271edf6e24f25b6b06f2767a3dfe3.r2.dev${path}`;
        const res2 = await originalFetch(r2Path);
        const data2 = await res2.json();
        CACHE[key] = data2;
        return data2;
      } catch (err2) {
        console.error(`[CLIENT_API] All fallbacks failed for ${path}:`, err2);
        throw err2;
      }
    }
  }

  function jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
      status,
      headers: {
        'Content-Type': 'application/json',
        'X-Powered-By': 'Serverless-Static-Engine'
      }
    });
  }

  window.fetch = async function (input, init) {
    let url = typeof input === 'string' ? input : (input && input.url ? input.url : '');

    if (url.startsWith('/api/')) {
      try {
        const u = new URL(url, window.location.origin);
        const path = u.pathname;
        const params = u.searchParams;

        // 1. /api/stats
        if (path === '/api/stats') {
          const stats = await loadData('stats', '/data/stats.json');
          return jsonResponse(stats);
        }

        // 2. /api/digimon-filters
        if (path === '/api/digimon-filters') {
          const filters = await loadData('filters', '/data/filters.json');
          return jsonResponse(filters);
        }

        // 3. /api/rank-table
        if (path === '/api/rank-table') {
          const rt = await loadData('rankTable', '/data/rank_table.json');
          return jsonResponse(rt);
        }

        // 4. /api/dungeons
        if (path === '/api/dungeons') {
          const d = await loadData('dungeons', '/data/dungeons.json');
          return jsonResponse(d);
        }

        // 5. /api/decks
        if (path === '/api/decks') {
          const d = await loadData('decks', '/data/decks.json');
          return jsonResponse(d);
        }

        // 6. /api/eggs
        if (path === '/api/eggs') {
          const d = await loadData('eggs', '/data/eggs.json');
          return jsonResponse(d);
        }

        // 7. /api/jogress-quests
        if (path === '/api/jogress-quests') {
          const d = await loadData('jogress', '/data/jogress.json');
          return jsonResponse(d);
        }

        // 8. /api/dunits
        if (path === '/api/dunits') {
          const d = await loadData('dunits', '/data/dunits.json');
          return jsonResponse(d);
        }

        // 9. /api/npc-exchange/:id
        if (path.startsWith('/api/npc-exchange/')) {
          const npcId = path.split('/')[3];
          const exch = await loadData('npcExchanges', '/data/npc_exchanges.json');
          const list = exch[npcId] || [];
          return jsonResponse(list);
        }

        // 10. /api/tamers
        if (path === '/api/tamers') {
          const raw = await loadData('tamers', '/data/tamers.json');
          return jsonResponse(raw.tamers || raw);
        }

        // 11. /api/tamers/:ref
        if (path.startsWith('/api/tamers/')) {
          const ref = decodeURIComponent(path.slice('/api/tamers/'.length)).toLowerCase().trim();
          const raw = await loadData('tamers', '/data/tamers.json');
          const tList = raw.tamers || raw;
          const found = tList.find(t => String(t.id) === ref || (t.slug && t.slug.toLowerCase() === ref) || (t.name && t.name.toLowerCase() === ref));
          if (!found) return jsonResponse({ detail: 'Not found' }, 404);
          return jsonResponse({
            tamer: found,
            skill_system: raw.skill_system || {},
            tamer_status: raw.tamer_status || {}
          });
        }

        // 12. /api/seals
        if (path === '/api/seals') {
          const s = await loadData('seals', '/data/seals.json');
          return jsonResponse(s);
        }

        // 13. /api/seals/:ref
        if (path.startsWith('/api/seals/')) {
          const ref = decodeURIComponent(path.slice('/api/seals/'.length)).toLowerCase().trim();
          const s = await loadData('seals', '/data/seals.json');
          const sealsList = s.seals || [];
          const found = sealsList.find(x => String(x.id) === ref || (x.slug && x.slug.toLowerCase() === ref) || (x.name && x.name.toLowerCase() === ref));
          if (!found) return jsonResponse({ detail: 'Not found' }, 404);
          return jsonResponse(found);
        }

        // 14. /api/patches/status
        if (path === '/api/patches/status') {
          const p = await loadData('patches', '/data/patches.json');
          return jsonResponse({ total: p.length, status: 'ok' });
        }

        // 15. /api/patches/:id
        if (path.startsWith('/api/patches/')) {
          const pid = decodeURIComponent(path.slice('/api/patches/'.length)).trim();
          const p = await loadData('patches', '/data/patches.json');
          const meta = p.find(x => x.id === pid);
          if (!meta) return jsonResponse({ detail: 'Patch not found' }, 404);

          let htmlContent = '';
          try {
            const hRes = await originalFetch(`/data/patches/${encodeURIComponent(pid)}.html`);
            if (hRes.ok) {
              htmlContent = await hRes.text();
            } else {
              const hRes2 = await originalFetch(`https://pub-f7d271edf6e24f25b6b06f2767a3dfe3.r2.dev/data/patches/${encodeURIComponent(pid)}.html`);
              if (hRes2.ok) htmlContent = await hRes2.text();
            }
          } catch (e) {
            console.warn('[CLIENT_API] Patch html fetch failed:', e);
          }

          return jsonResponse({ ...meta, html: htmlContent });
        }

        // 16. /api/patches
        if (path === '/api/patches') {
          const p = await loadData('patches', '/data/patches.json');
          return jsonResponse({ items: p, total: p.length });
        }

        // 17. /api/digimon/:slug
        if (path.startsWith('/api/digimon/')) {
          const slug = decodeURIComponent(path.slice('/api/digimon/'.length)).toLowerCase().trim();
          const digiList = await loadData('digimon', '/data/digimon.json');
          if (CACHE.digimonBySlug.size === 0) {
            for (const d of digiList) {
              if (d.slug) CACHE.digimonBySlug.set(d.slug.toLowerCase(), d);
              if (d.title) CACHE.digimonBySlug.set(d.title.toLowerCase(), d);
            }
          }
          const found = CACHE.digimonBySlug.get(slug);
          if (!found) return jsonResponse({ detail: 'Digimon not found' }, 404);
          return jsonResponse({ digimon: found });
        }

        // 18. /api/digimon?... (Search, Filter, Sort, Paginate)
        if (path === '/api/digimon') {
          const digiList = await loadData('digimon', '/data/digimon.json');
          let results = digiList;

          const q = (params.get('q') || '').toLowerCase().trim();
          const rank = params.get('rank');
          const attribute = params.get('attribute');
          const element = params.get('element');
          const sort = params.get('sort') || 'rank';
          const offset = parseInt(params.get('offset') || '0', 10);
          const limit = parseInt(params.get('limit') || '40', 10);

          function num(d, k) {
            try {
              const val = (d.stats && d.stats[k] && d.stats[k].max) ? d.stats[k].max.replace('%', '') : '-1';
              return parseFloat(val) || -1;
            } catch (e) { return -1; }
          }

          if (sort === 'name') {
            results = [...results].sort((a, b) => (a.title || '').localeCompare(b.title || ''));
          } else if (sort === 'at' || sort === 'hp') {
            const k = sort.toUpperCase();
            results = [...results].sort((a, b) => num(b, k) - num(a, k));
          }

          if (q) {
            results = results.filter(d =>
              (d.title && d.title.toLowerCase().includes(q)) ||
              (d.thai_name && d.thai_name.toLowerCase().includes(q)) ||
              (d.slug && d.slug.toLowerCase().includes(q))
            );
          }

          if (rank && rank !== 'all') {
            if (rank === 'none') {
              results = results.filter(d => !d.rank);
            } else {
              results = results.filter(d => d.rank && d.rank.toUpperCase() === rank.toUpperCase());
            }
          }

          if (attribute && attribute !== 'all') {
            results = results.filter(d => d.attribute && d.attribute.toLowerCase() === attribute.toLowerCase());
          }

          if (element && element !== 'all') {
            results = results.filter(d => d.element && d.element.toLowerCase() === element.toLowerCase());
          }

          const total = results.length;
          const pagedItems = results.slice(offset, offset + limit);

          return jsonResponse({ total, items: pagedItems });
        }
      } catch (err) {
        console.error('[CLIENT_API] Error processing API request:', url, err);
      }
    }

    return originalFetch.apply(this, arguments);
  };

  console.log('[CLIENT_API] ⚡ Serverless Client-Side API Engine Ready!');
})();
