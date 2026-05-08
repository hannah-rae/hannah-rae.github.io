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

})();
