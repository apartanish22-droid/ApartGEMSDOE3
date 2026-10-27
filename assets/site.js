(() => {
  "use strict";

  const root = document.body?.dataset?.projectRoot || ".";
  const jsonUrl = (file) => new URL(`${root}/docs/data/${file}`, document.baseURI).href;
  const percent = (value) => `${(Number(value) * 100).toFixed(1)}%`;

  function makeCell(content, className = "") {
    const td = document.createElement("td");
    if (className) td.className = className;
    if (content instanceof Node) td.append(content);
    else td.textContent = String(content);
    return td;
  }

  function renderSites(data) {
    const tbody = document.getElementById("focus-site-rows");
    if (!tbody) return;
    if (!Array.isArray(data.sites) || data.sites.length !== 9) {
      throw new Error("The focus-site audit record did not contain the expected nine entries.");
    }

    const fragment = document.createDocumentFragment();
    data.sites.forEach((site) => {
      const row = document.createElement("tr");
      const name = document.createElement("span");
      name.className = "site-name";
      name.textContent = site.site;
      row.append(makeCell(name));

      const methodCell = document.createElement("td");
      const method = document.createElement("span");
      method.className = "method-label";
      method.textContent = site.method_tag;
      const methodNote = document.createElement("span");
      methodNote.className = "score-provenance method-note";
      methodNote.textContent = site.method_note;
      methodCell.append(method, methodNote);
      row.append(methodCell);

      const artifactCell = document.createElement("td");
      const artifact = document.createElement("code");
      artifact.className = "artifact-name";
      artifact.textContent = site.file;
      const hash = document.createElement("span");
      hash.className = "score-provenance";
      hash.textContent = `SHA-256 ${String(site.sha256).slice(0, 12)}… · research only`;
      artifactCell.append(artifact, hash);
      row.append(artifactCell);

      const scoreCell = document.createElement("td");
      const score = document.createElement("span");
      score.className = "score-value";
      score.textContent = Number(site.reported_score).toFixed(4);
      const provenance = document.createElement("span");
      provenance.className = "score-provenance";
      provenance.textContent = "OWNER-REPORTED";
      scoreCell.append(score, provenance);
      row.append(scoreCell);

      row.append(makeCell(percent(site.max_overlap_vs_other_eight), "audit-value audit-fail"));
      row.append(makeCell(Number(site.max_abs_binary_surface_spearman_vs_other_eight).toFixed(3), "audit-value"));

      const statusCell = document.createElement("td");
      const status = document.createElement("span");
      status.className = "status-pill";
      status.textContent = "FAIL · NOT UNIQUE";
      statusCell.append(status);
      row.append(statusCell);
      fragment.append(row);
    });
    tbody.replaceChildren(fragment);
  }

  function renderLeaderboard(data) {
    const target = document.getElementById("leaderboard-top");
    if (!target) return;
    const leader = Array.isArray(data.rows) ? data.rows.find((row) => row.rank === 1) : null;
    if (!leader || !Number.isFinite(Number(leader.public_score))) {
      throw new Error("The dated public leaderboard snapshot has no valid first row.");
    }

    const rank = document.createElement("span");
    rank.className = "leader-rank";
    rank.textContent = `Rank #${leader.rank} · ${data.observed_on_utc}`;
    const score = document.createElement("span");
    score.className = "leader-score";
    score.textContent = Number(leader.public_score).toFixed(4);
    const participant = document.createElement("span");
    participant.className = "leader-participant";
    participant.textContent = leader.participant;
    const label = document.createElement("span");
    label.className = "leader-label";
    label.textContent = "ORGANIZER PUBLIC-LEADERBOARD SNAPSHOT · NOT A SUBMISSION RECEIPT";
    target.replaceChildren(rank, score, participant, label);
  }

  function reportLoadFailure(id, sourcePath) {
    const target = document.getElementById(id);
    if (!target) return;
    target.replaceChildren();
    const message = document.createElement(id === "focus-site-rows" ? "td" : "span");
    message.className = "loading-cell";
    message.textContent = "Could not load the dated local audit record. ";
    if (message.tagName === "TD") message.colSpan = 7;
    const link = document.createElement("a");
    link.href = sourcePath;
    link.textContent = "Open the source JSON";
    message.append(link);
    target.append(message);
  }

  fetch(jsonUrl("focus-sites.json"), { cache: "no-cache" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(renderSites)
    .catch((error) => {
      // Keep the pre-rendered historical table visible if enhancement fails.
      console.warn("Could not enhance the static focus-site table from JSON.", error);
    });

  fetch(jsonUrl("leaderboard.json"), { cache: "no-cache" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(renderLeaderboard)
    .catch(() => reportLoadFailure("leaderboard-top", "docs/data/leaderboard.json"));
})();
