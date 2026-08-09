/* =====================================================
   Hannah Kerner — site behaviors
   - Email obfuscation against scrapers
   - Live GitHub stars/forks for code & data cards
   ===================================================== */

(function () {

  // ---- Email obfuscation -------------------------------------------------
  // Email is never written to static HTML. Markup contains:
  //   <a class="protected-email" data-u="user" data-d="domain.tld" href="#">email</a>
  // JS assembles the address at runtime using fromCharCode for the @ sign,
  // so even an HTML scrape that looks for an @ symbol will come up empty.
  document.querySelectorAll('.protected-email').forEach(function (el) {
    var u = el.dataset.u, d = el.dataset.d;
    if (!u || !d) return;
    var addr = u + String.fromCharCode(64) + d;
    el.textContent = addr;
    el.setAttribute('aria-label', 'Email ' + addr);
    el.addEventListener('click', function (e) {
      e.preventDefault();
      window.location.href = 'mailto:' + addr;
    });
  });

  // ---- GitHub repo stats -------------------------------------------------
  // Cards with [data-repo="owner/name"] get live stargazers / forks counts.
  // Cached in localStorage for 6h to avoid hammering the API.
  var SIX_HOURS = 6 * 60 * 60 * 1000;

  document.querySelectorAll('[data-repo]').forEach(function (card) {
    var repo = card.getAttribute('data-repo');
    var starsEl = card.querySelector('.stars');
    var forksEl = card.querySelector('.forks');
    if (!starsEl && !forksEl) return;
    var key = 'gh:' + repo;

    var cached = null;
    try {
      var raw = localStorage.getItem(key);
      if (raw) cached = JSON.parse(raw);
    } catch (e) {}

    if (cached && (Date.now() - cached.at) < SIX_HOURS) {
      apply(cached.d);
      return;
    }

    fetch('https://api.github.com/repos/' + repo)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j) return apply(null);
        var d = { stars: j.stargazers_count, forks: j.forks_count };
        try { localStorage.setItem(key, JSON.stringify({ at: Date.now(), d: d })); } catch (e) {}
        apply(d);
      })
      .catch(function () { apply(null); });

    function apply(d) {
      if (starsEl) starsEl.textContent = d ? d.stars.toLocaleString() : '—';
      if (forksEl) forksEl.textContent = d ? d.forks.toLocaleString() : '—';
    }
  });

  // ---- Zenodo download stats ----------------------------------------------
  // Dataset cards may also declare [data-zenodo] with either a record URL or
  // a community records URL. We fetch downloads live and cache for 6h.
  document.querySelectorAll('[data-zenodo]').forEach(function (card) {
    var zenodoUrl = card.getAttribute('data-zenodo');
    var downloadsEl = card.querySelector('.zenodo-downloads');
    if (!zenodoUrl || !downloadsEl) return;

    var source = parseZenodoSource(zenodoUrl);
    if (!source) {
      downloadsEl.textContent = '—';
      return;
    }

    var key = 'zenodo:' + source.kind + ':' + source.id;

    var cached = null;
    try {
      var raw = localStorage.getItem(key);
      if (raw) cached = JSON.parse(raw);
    } catch (e) {}

    if (cached && (Date.now() - cached.at) < SIX_HOURS) {
      apply(cached.d);
      return;
    }

    fetch(source.api)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        var d = getZenodoDownloads(source, j);
        try { localStorage.setItem(key, JSON.stringify({ at: Date.now(), d: d })); } catch (e) {}
        apply(d);
      })
      .catch(function () { apply(null); });

    function apply(d) {
      downloadsEl.textContent = (d && typeof d.downloads === 'number') ? d.downloads.toLocaleString() : '—';
    }
  });

  function parseZenodoSource(url) {
    var recordMatch = url.match(/zenodo\.org\/records\/(\d+)/i);
    if (recordMatch) {
      return {
        kind: 'record',
        id: recordMatch[1],
        api: 'https://zenodo.org/api/records/' + recordMatch[1]
      };
    }

    var communityMatch = url.match(/zenodo\.org\/communities\/([^/?#]+)/i);
    if (communityMatch) {
      var community = communityMatch[1];
      return {
        kind: 'community',
        id: community,
        api: 'https://zenodo.org/api/records?q=' + encodeURIComponent('communities:' + community) + '&size=100'
      };
    }

    return null;
  }

  function getZenodoDownloads(source, payload) {
    if (!payload) return null;

    if (source.kind === 'record') {
      if (!payload.stats || typeof payload.stats.downloads !== 'number') return null;
      return { downloads: payload.stats.downloads };
    }

    if (source.kind === 'community') {
      var hits = payload.hits && payload.hits.hits;
      if (!Array.isArray(hits)) return null;
      return {
        downloads: hits.reduce(function (sum, hit) {
          var count = hit && hit.stats && typeof hit.stats.downloads === 'number' ? hit.stats.downloads : 0;
          return sum + count;
        }, 0)
      };
    }

    return null;
  }

})();
