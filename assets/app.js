(() => {
  const script = document.currentScript;
  if (!script) return;
  const feedUrl = new URL('../docs/data/live_feed.json', script.src);
  const setText = (id, text) => {
    const element = document.getElementById(id);
    if (element) element.textContent = text;
  };
  fetch(feedUrl, {cache: 'no-store'})
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(feed => {
      const board = feed.leaderboard;
      if (board && Number.isFinite(board.value) && board.value >= 0 && board.value <= 1 && board.observed_utc) {
        setText('live-score', board.value.toFixed(4));
        const observed = new Date(board.observed_utc);
        if (!Number.isNaN(observed.getTime())) {
          const hours = (Date.now() - observed.getTime()) / 3600000;
          const age = hours < 0 || hours > 24 ? ' · snapshot may be stale' : '';
          setText('live-time', `Public leaderboard · observed ${observed.toISOString().replace('T', ' ').slice(0, 16)} UTC${age}`);
        }
      }
      if (feed.leaderboard_status === 'skipped') {
        setText('feed-warning', 'The latest refresh skipped the leaderboard; the dated observation was retained.');
      } else if (feed.leaderboard_error) {
        setText('feed-warning', 'Latest leaderboard refresh failed; the dated snapshot above was retained.');
      }
      const heads = Object.values(feed.site_heads || {});
      const failures = Object.keys(feed.site_head_errors || {}).length;
      if (heads.length) {
        const times = heads.map(head => new Date(head.observed_utc).getTime()).filter(Number.isFinite).sort((a, b) => a - b);
        const formatted = value => new Date(value).toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
        const span = !times.length ? 'unknown' : times[0] === times[times.length - 1]
          ? formatted(times[0]) : `${formatted(times[0])}–${formatted(times[times.length - 1])}`;
        const check = feed.site_heads_status === 'skipped' ? 'latest check skipped' : `${failures} latest check errors`;
        setText('head-feed', `${heads.length} source-head snapshots observed ${span}; ${check}. Changes require a new scientific audit.`);
      }
    })
    .catch(() => setText('feed-warning', 'Live feed unavailable; use the dated snapshot and official leaderboard link.'));
})();
