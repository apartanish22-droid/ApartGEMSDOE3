/* Source freshness only: a changed or unavailable head never authorizes a file. */
(() => {
  const status = document.querySelector('[data-source-status]');
  const button = document.querySelector('[data-refresh-sources]');
  if (!status || !button) return;

  async function fetchJson(url) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, { cache: 'no-store', signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally { clearTimeout(timeout); }
  }

  async function checkSources() {
    button.disabled = true;
    status.textContent = 'Checking pinned repository heads…';
    try {
      const manifest = await fetchJson('registry/focus_sites.json');
      if (!Array.isArray(manifest.sites) || manifest.sites.length !== 9) throw new Error('Invalid source list');
      const checks = await Promise.allSettled(manifest.sites.map(async (site) => {
        if (!/^buffedlizard55-lab\/GEMSDOE\d+$/.test(site.repo) || !/^[a-f0-9]{40}$/.test(site.ref)) {
          throw new Error('Invalid pinned repository');
        }
        const head = await fetchJson(`https://api.github.com/repos/${site.repo}/commits/main`);
        if (!/^[a-f0-9]{40}$/.test(head.sha || '')) throw new Error('Invalid GitHub response');
        return head.sha === site.ref;
      }));
      const unknown = checks.filter((item) => item.status !== 'fulfilled').length;
      const changed = checks.filter((item) => item.status === 'fulfilled' && !item.value).length;
      const time = new Date().toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
      if (unknown) status.textContent = `Freshness unknown for ${unknown} source(s); ${changed} changed. Re-audit required. Checked ${time}.`;
      else if (changed) status.textContent = `${changed} source(s) changed since the audit; re-audit required. Checked ${time}.`;
      else status.textContent = `All nine historical source heads unchanged at ${time}; the lattice and wider registry were not checked.`;
    } catch (_) {
      status.textContent = 'Source freshness unavailable. Do not assume this snapshot is current.';
    } finally { button.disabled = false; }
  }

  button.addEventListener('click', checkSources);
  checkSources();
})();
