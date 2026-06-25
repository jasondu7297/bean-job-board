(() => {
  "use strict";

  const board = window.JOB_BOARD_DATA || { meta: {}, profile: {}, jobs: [] };
  const PAGE_SIZE = 60;
  const STORAGE_KEYS = {
    saved: "celina-job-board-saved-v2",
  };

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const elements = {
    title: $("#board-title"),
    summary: $("#profile-summary"),
    refreshLabel: $("#refresh-label"),
    refreshLive: $("#refresh-live"),
    statusDot: $("#status-dot"),
    total: $("#metric-total"),
    new: $("#metric-new"),
    strong: $("#metric-strong"),
    research: $("#metric-research"),
    recent: $("#metric-recent"),
    syncHeading: $("#sync-heading"),
    syncDetail: $("#sync-detail"),
    syncProgressBar: $("#sync-progress-bar"),
    search: $("#search-input"),
    category: $("#category-filter"),
    location: $("#location-filter"),
    source: $("#source-filter"),
    fit: $("#fit-filter"),
    age: $("#age-filter"),
    sort: $("#sort-filter"),
    researchOnly: $("#research-only"),
    entryOnly: $("#entry-only"),
    newOnly: $("#new-only"),
    clear: $("#clear-filters"),
    export: $("#export-visible"),
    allView: $("#view-all"),
    savedView: $("#view-saved"),
    savedCount: $("#saved-count"),
    resultCount: $("#result-count"),
    grid: $("#job-grid"),
    empty: $("#empty-state"),
    emptyClear: $("#empty-clear"),
    loadMoreWrap: $("#load-more-wrap"),
    loadMore: $("#load-more"),
    loadMoreNote: $("#load-more-note"),
    disclaimer: $("#disclaimer"),
    sourceHealth: $("#source-health"),
    sourceTableBody: $("#source-table-body"),
    template: $("#job-card-template"),
    detailsDialog: $("#details-dialog"),
    detailsContent: $("#details-content"),
    emailDialog: $("#email-dialog"),
    emailHeading: $("#email-heading"),
    emailSubject: $("#email-subject"),
    emailBody: $("#email-body"),
    copyEmail: $("#copy-email"),
    copyStatus: $("#copy-status"),
  };

  function loadSaved() {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEYS.saved) || "[]");
      return new Set(Array.isArray(value) ? value : []);
    } catch {
      return new Set();
    }
  }

  const state = {
    jobs: Array.isArray(board.jobs) ? board.jobs : [],
    filtered: [],
    saved: loadSaved(),
    view: "all",
    displayLimit: PAGE_SIZE,
    sourceStats: Array.isArray(board.meta?.source_health) ? board.meta.source_health : [],
    syncing: false,
    liveNewCount: Number(board.meta?.new_since_previous || 0),
  };

  function saveSaved() {
    try {
      localStorage.setItem(STORAGE_KEYS.saved, JSON.stringify([...state.saved]));
    } catch {
      // Browser storage may be disabled; the in-memory saved list still works.
    }
    elements.savedCount.textContent = String(state.saved.size);
  }

  function clean(value) {
    return String(value ?? "").replace(/\s+/g, " ").trim();
  }

  function safeUrl(value) {
    try {
      const url = new URL(String(value || ""), window.location.href);
      return /^https?:$/.test(url.protocol) ? url.toString() : "";
    } catch {
      return "";
    }
  }

  function formatRefresh(value) {
    const date = value ? new Date(value) : null;
    if (!date || Number.isNaN(date.getTime())) return "Refresh time unavailable";
    return `Synced ${new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
    }).format(date)}`;
  }

  function postedLabel(job) {
    if (Number.isFinite(job.age_days)) {
      if (job.age_days === 0) return "Today";
      if (job.age_days === 1) return "1 day ago";
      if (job.age_days < 60) return `${job.age_days} days ago`;
      const months = Math.max(2, Math.round(job.age_days / 30));
      return `${months} months ago`;
    }
    if (job.posted_at) {
      const date = new Date(`${job.posted_at}T12:00:00`);
      if (!Number.isNaN(date.getTime())) {
        return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
      }
    }
    return "Date not listed";
  }

  function addTag(container, text, className = "") {
    if (!text) return;
    const tag = document.createElement("span");
    tag.className = `tag ${className}`.trim();
    tag.textContent = text;
    container.append(tag);
  }

  function addMeta(container, value) {
    if (!value) return;
    const span = document.createElement("span");
    span.textContent = value;
    container.append(span);
  }

  function fitClass(tier) {
    return {
      Strong: "fit-badge--strong",
      Good: "fit-badge--good",
      Stretch: "fit-badge--stretch",
    }[tier] || "fit-badge--low";
  }

  function toggleSaved(job, button) {
    if (state.saved.has(job.id)) state.saved.delete(job.id);
    else state.saved.add(job.id);
    button.classList.toggle("is-saved", state.saved.has(job.id));
    button.setAttribute("aria-label", state.saved.has(job.id) ? "Remove saved job" : "Save job");
    saveSaved();
    if (state.view === "saved") applyFilters(false);
  }

  function renderCard(job) {
    const fragment = elements.template.content.cloneNode(true);
    const card = $(".job-card", fragment);
    const badge = $(".fit-badge", fragment);
    badge.classList.add(fitClass(job.fit_tier));
    badge.textContent = `${job.fit_tier || "Match"} · ${Math.round(Number(job.match_score || 0))}`;

    const newBadge = $(".new-badge", fragment);
    newBadge.hidden = !job.is_new;
    $(".posted-label", fragment).textContent = postedLabel(job);
    $(".job-title", fragment).textContent = job.title || "Untitled role";
    $(".job-company", fragment).textContent = job.company || "Company not listed";

    const saveButton = $(".save-button", fragment);
    saveButton.classList.toggle("is-saved", state.saved.has(job.id));
    saveButton.setAttribute("aria-label", state.saved.has(job.id) ? "Remove saved job" : "Save job");
    saveButton.addEventListener("click", () => toggleSaved(job, saveButton));

    const meta = $(".job-meta", fragment);
    addMeta(meta, job.location);
    addMeta(meta, job.workplace);
    addMeta(meta, job.salary);
    addMeta(meta, job.source);

    $(".job-summary", fragment).textContent = job.summary || job.description || "Open the posting for full role details.";
    const categories = $(".category-tags", fragment);
    addTag(categories, job.category || "General New Grad", "tag--category");
    if (job.research) addTag(categories, "Research", "tag--research");
    if (job.entry_level) addTag(categories, "Entry level");

    const skills = $(".skill-tags", fragment);
    const matched = Array.isArray(job.matched_skills) ? job.matched_skills.slice(0, 6) : [];
    if (matched.length) matched.forEach((skill) => addTag(skills, skill));
    else addTag(skills, "Category and experience match");

    const warning = $(".job-warning", fragment);
    const warnings = Array.isArray(job.warnings) ? job.warnings.filter(Boolean) : [];
    if (warnings.length) {
      warning.textContent = warnings.slice(0, 2).join(" · ");
      warning.hidden = false;
    }

    const apply = $(".apply-link", fragment);
    const url = safeUrl(job.apply_url || job.url);
    if (url) apply.href = url;
    else {
      apply.removeAttribute("href");
      apply.textContent = "Posting link unavailable";
      apply.setAttribute("aria-disabled", "true");
      apply.classList.add("is-disabled");
    }

    $(".details-button", fragment).addEventListener("click", () => openDetails(job));
    const emailButton = $(".email-button", fragment);
    if (job.cold_email) {
      emailButton.hidden = false;
      emailButton.addEventListener("click", () => openEmail(job));
    }

    card.dataset.jobId = job.id || "";
    return fragment;
  }

  function section(title, content) {
    const wrapper = document.createElement("section");
    wrapper.className = "modal__section";
    const heading = document.createElement("h3");
    heading.textContent = title;
    wrapper.append(heading, content);
    return wrapper;
  }

  function paragraph(text) {
    const p = document.createElement("p");
    p.textContent = text;
    return p;
  }

  function list(values) {
    const ul = document.createElement("ul");
    ul.className = "modal__list";
    values.forEach((value) => {
      const li = document.createElement("li");
      li.textContent = value;
      ul.append(li);
    });
    return ul;
  }

  function openDetails(job) {
    elements.detailsContent.replaceChildren();
    const title = document.createElement("h2");
    title.className = "modal__title";
    title.textContent = job.title;
    const company = document.createElement("p");
    company.className = "modal__company";
    company.textContent = `${job.company}${job.location ? ` · ${job.location}` : ""}`;
    elements.detailsContent.append(title, company);

    const facts = [];
    if (job.category) facts.push(`Category: ${job.category}`);
    if (job.fit_tier) facts.push(`Resume fit: ${job.fit_tier} (${Math.round(Number(job.match_score || 0))}/100)`);
    if (job.posted_at || Number.isFinite(job.age_days)) facts.push(`Posted: ${postedLabel(job)}`);
    if (job.salary) facts.push(`Compensation: ${job.salary}`);
    if (job.workplace) facts.push(`Work model: ${job.workplace}`);
    if (job.source) facts.push(`Source: ${job.source}`);
    elements.detailsContent.append(section("At a glance", list(facts)));

    elements.detailsContent.append(section(
      "Role summary",
      paragraph(job.description || job.summary || "Open the employer posting for complete responsibilities and qualifications."),
    ));

    const skills = Array.isArray(job.matched_skills) ? job.matched_skills : [];
    if (skills.length) elements.detailsContent.append(section("Resume overlap", list(skills)));
    const warnings = Array.isArray(job.warnings) ? job.warnings : [];
    if (warnings.length) elements.detailsContent.append(section("Items to verify", list(warnings)));

    const actions = document.createElement("div");
    actions.className = "modal__actions";
    const apply = document.createElement("a");
    apply.className = "button button--primary";
    apply.href = safeUrl(job.apply_url || job.url) || "#";
    apply.target = "_blank";
    apply.rel = "noopener noreferrer";
    apply.textContent = "Open posting";
    actions.append(apply);
    if (job.cold_email) {
      const emailButton = document.createElement("button");
      emailButton.className = "button button--secondary";
      emailButton.type = "button";
      emailButton.textContent = "Open cold email";
      emailButton.addEventListener("click", () => {
        elements.detailsDialog.close();
        openEmail(job);
      });
      actions.append(emailButton);
    }
    elements.detailsContent.append(actions);
    elements.detailsDialog.showModal();
  }

  function openEmail(job) {
    const email = job.cold_email;
    if (!email) return;
    elements.emailHeading.textContent = `${job.company}: ${job.title}`;
    elements.emailSubject.value = email.subject || "";
    elements.emailBody.value = email.body || "";
    elements.copyStatus.textContent = "";
    elements.emailDialog.showModal();
  }

  async function copyEmail() {
    const text = `Subject: ${elements.emailSubject.value}\n\n${elements.emailBody.value}`;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const temp = document.createElement("textarea");
      temp.value = text;
      temp.style.position = "fixed";
      temp.style.opacity = "0";
      document.body.append(temp);
      temp.select();
      document.execCommand("copy");
      temp.remove();
    }
    elements.copyStatus.textContent = "Copied";
    window.setTimeout(() => { elements.copyStatus.textContent = ""; }, 1800);
  }

  function searchText(job) {
    return [
      job.title,
      job.company,
      job.location,
      job.location_group,
      job.category,
      job.source,
      job.description,
      ...(job.matched_skills || []),
      ...(job.secondary_categories || []),
    ].join(" ").toLowerCase();
  }

  function filteredJobs() {
    const query = elements.search.value.trim().toLowerCase();
    const category = elements.category.value;
    const location = elements.location.value;
    const source = elements.source.value;
    const fit = elements.fit.value;
    const age = elements.age.value;

    const jobs = state.jobs.filter((job) => {
      if (state.view === "saved" && !state.saved.has(job.id)) return false;
      if (query && !searchText(job).includes(query)) return false;
      if (category && job.category !== category && !(job.secondary_categories || []).includes(category)) return false;
      if (location && job.location_group !== location) return false;
      if (source && job.source !== source) return false;
      if (fit && job.fit_tier !== fit) return false;
      if (elements.researchOnly.checked && !job.research) return false;
      if (elements.entryOnly.checked && !job.entry_level) return false;
      if (elements.newOnly.checked && !job.is_new) return false;
      if (age === "unknown" && job.age_days !== null && job.age_days !== undefined) return false;
      if (age && age !== "unknown") {
        const limit = Number(age);
        if (!Number.isFinite(job.age_days) || job.age_days > limit) return false;
      }
      return true;
    });

    const sort = elements.sort.value;
    jobs.sort((a, b) => {
      if (sort === "newest") {
        return String(b.posted_at || "").localeCompare(String(a.posted_at || ""))
          || Number(b.match_score || 0) - Number(a.match_score || 0);
      }
      if (sort === "new") {
        return Number(Boolean(b.is_new)) - Number(Boolean(a.is_new))
          || String(b.posted_at || "").localeCompare(String(a.posted_at || ""))
          || Number(b.match_score || 0) - Number(a.match_score || 0);
      }
      if (sort === "company") {
        return String(a.company || "").localeCompare(String(b.company || ""))
          || Number(b.match_score || 0) - Number(a.match_score || 0);
      }
      return Number(b.match_score || 0) - Number(a.match_score || 0)
        || String(b.posted_at || "").localeCompare(String(a.posted_at || ""));
    });
    return jobs;
  }

  function applyFilters(resetLimit = true) {
    if (resetLimit) state.displayLimit = PAGE_SIZE;
    state.filtered = filteredJobs();
    elements.resultCount.textContent = state.filtered.length.toLocaleString("en-US");
    const visible = state.filtered.slice(0, state.displayLimit);
    elements.grid.replaceChildren(...visible.map(renderCard));
    elements.grid.hidden = state.filtered.length === 0;
    elements.empty.hidden = state.filtered.length !== 0;
    elements.allView.classList.toggle("is-active", state.view === "all");
    elements.savedView.classList.toggle("is-active", state.view === "saved");

    const remaining = Math.max(0, state.filtered.length - visible.length);
    elements.loadMoreWrap.hidden = remaining === 0;
    elements.loadMoreNote.textContent = remaining
      ? `Showing ${visible.length.toLocaleString("en-US")} of ${state.filtered.length.toLocaleString("en-US")}`
      : "";
    saveSaved();
  }

  function resetFilters() {
    elements.search.value = "";
    elements.category.value = "";
    elements.location.value = "";
    elements.source.value = "";
    elements.fit.value = "";
    elements.age.value = "";
    elements.sort.value = "score";
    elements.researchOnly.checked = false;
    elements.entryOnly.checked = false;
    elements.newOnly.checked = false;
    state.view = "all";
    applyFilters(true);
  }

  function exportFiltered() {
    const columns = [
      "is_new", "match_score", "fit_tier", "title", "company", "location", "location_group",
      "category", "research", "posted_at", "salary", "source", "url", "matched_skills", "warnings",
    ];
    const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
    const rows = [columns.join(",")];
    state.filtered.forEach((job) => {
      const row = { ...job };
      row.matched_skills = (job.matched_skills || []).join("; ");
      row.warnings = (job.warnings || []).join("; ");
      rows.push(columns.map((column) => escape(row[column])).join(","));
    });
    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `celina-job-board-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function replaceSelectOptions(select, values, defaultLabel) {
    const selected = select.value;
    select.replaceChildren();
    const base = document.createElement("option");
    base.value = "";
    base.textContent = defaultLabel;
    select.append(base);
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.append(option);
    });
    if (values.includes(selected)) select.value = selected;
  }

  function refreshFilterOptions() {
    const unique = (field) => [...new Set(state.jobs.map((job) => clean(job[field])).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    replaceSelectOptions(elements.category, unique("category"), "All categories");
    replaceSelectOptions(elements.location, unique("location_group"), "All U.S. locations");
    replaceSelectOptions(elements.source, unique("source"), "All sources");
  }

  function updateMetrics(newCount = state.liveNewCount) {
    elements.total.textContent = state.jobs.length.toLocaleString("en-US");
    elements.new.textContent = Number(newCount || 0).toLocaleString("en-US");
    elements.strong.textContent = state.jobs.filter((job) => job.fit_tier === "Strong").length.toLocaleString("en-US");
    elements.research.textContent = state.jobs.filter((job) => job.research).length.toLocaleString("en-US");
    elements.recent.textContent = state.jobs.filter((job) => Number.isFinite(job.age_days) && job.age_days <= 7).length.toLocaleString("en-US");
  }

  function updateSourceTable(stats) {
    elements.sourceTableBody.replaceChildren();
    stats.forEach((row) => {
      const tr = document.createElement("tr");
      const source = document.createElement("td");
      source.textContent = row.source || "Unknown source";
      const status = document.createElement("td");
      const pill = document.createElement("span");
      pill.className = `source-status source-status--${row.status === "ok" || row.status === "offline" ? "ok" : "error"}`;
      pill.textContent = row.status === "ok" ? "Live" : row.status === "offline" ? "Bundled" : "Temporary error";
      status.append(pill);
      const fetched = document.createElement("td");
      fetched.textContent = Number(row.fetched || 0).toLocaleString("en-US");
      tr.append(source, status, fetched);
      elements.sourceTableBody.append(tr);
    });
  }

  function setSyncProgress(completed, total) {
    const percent = total ? Math.max(0, Math.min(100, (completed / total) * 100)) : 0;
    elements.syncProgressBar.style.width = `${percent}%`;
  }

  async function hydrateLive(force = false) {
    if (state.syncing) return;
    if (typeof window.fetchLiveJobFeeds !== "function") {
      elements.syncHeading.textContent = "Live-source loader was not available";
      elements.syncDetail.textContent = "The bundled snapshot remains usable. Open the deployable project through a web server or GitHub Pages for automatic refreshes.";
      return;
    }

    state.syncing = true;
    elements.refreshLive.disabled = true;
    elements.statusDot.classList.remove("status-dot--error");
    elements.statusDot.classList.add("status-dot--loading");
    elements.syncHeading.textContent = force ? "Refreshing all live sources…" : "Fetching comprehensive live sources…";
    elements.syncDetail.textContent = `Checking ${window.LIVE_JOB_SOURCES?.length || "multiple"} daily-maintained feeds. The bundled fallback remains visible while this runs; the final live count normally reaches hundreds.`;
    elements.refreshLabel.textContent = "Live refresh in progress";
    setSyncProgress(0, window.LIVE_JOB_SOURCES?.length || 1);

    try {
      const result = await window.fetchLiveJobFeeds(board, {
        force,
        onProgress(progress) {
          setSyncProgress(progress.completed, progress.total);
          elements.syncDetail.textContent = `${progress.completed} of ${progress.total} sources checked · ${progress.source}${progress.error ? " had a temporary error" : ` returned ${Number(progress.fetched || 0).toLocaleString("en-US")} U.S. roles`}`;
        },
      });
      state.jobs = result.jobs;
      state.sourceStats = result.sourceStats;
      state.liveNewCount = result.newCount;
      refreshFilterOptions();
      updateMetrics(result.newCount);
      updateSourceTable(result.sourceStats);
      applyFilters(true);
      setSyncProgress(result.totalSources, result.totalSources);
      elements.refreshLabel.textContent = formatRefresh(result.generatedAt);
      elements.syncHeading.textContent = `${state.jobs.length.toLocaleString("en-US")} unique U.S. matches are ready`;
      const failureText = result.failedSources
        ? ` ${result.failedSources} source${result.failedSources === 1 ? "" : "s"} had a temporary error and can be retried.`
        : " All live feeds completed successfully.";
      const baselineText = result.hadHistoryBaseline
        ? `${result.newCount.toLocaleString("en-US")} were not present at the previous browser sync.`
        : `${result.newCount.toLocaleString("en-US")} are marked new based on posting age; this browser now has a comparison baseline.`;
      elements.syncDetail.textContent = `${result.grossFetched.toLocaleString("en-US")} source rows were collected before deduplication. ${baselineText}${failureText}`;
      elements.sourceHealth.textContent = `${result.successfulSources} of ${result.totalSources} browser feeds completed; ${result.grossFetched.toLocaleString("en-US")} U.S. rows were retained before deduplication. The scheduled build separately checks employer ATS feeds.`;
      elements.statusDot.classList.remove("status-dot--loading");
      if (result.failedSources === result.totalSources) elements.statusDot.classList.add("status-dot--error");
    } catch (error) {
      elements.syncHeading.textContent = "Live refresh could not complete";
      elements.syncDetail.textContent = `The bundled snapshot is still available. Retry the live refresh when connected to the internet. ${clean(error?.message || "")}`;
      elements.refreshLabel.textContent = "Bundled snapshot shown";
      elements.statusDot.classList.remove("status-dot--loading");
      elements.statusDot.classList.add("status-dot--error");
    } finally {
      state.syncing = false;
      elements.refreshLive.disabled = false;
    }
  }

  function initialize() {
    const meta = board.meta || {};
    elements.title.textContent = meta.title || "Celina's Comprehensive New-Grad Job Board";
    elements.summary.textContent = board.profile?.summary || "Resume-matched U.S. opportunities across biology, bioinformatics, data, engineering, product, operations, and research.";
    elements.refreshLabel.textContent = meta.generated_at ? formatRefresh(meta.generated_at) : "Bundled snapshot loaded";
    elements.disclaimer.textContent = meta.disclaimer || "This board combines high-volume new-grad feeds with employer and research-institution sources. Coverage is broad but cannot be literally exhaustive. Verify that every role remains open and confirm work-authorization, degree, and experience requirements on the employer site.";
    elements.sourceHealth.textContent = state.sourceStats.length
      ? `${state.sourceStats.length} bundled source-status records are available; live browser feeds are being checked now.`
      : "Live browser feeds are being checked now.";
    elements.savedCount.textContent = String(state.saved.size);
    refreshFilterOptions();
    updateMetrics();
    updateSourceTable(state.sourceStats);
    applyFilters(true);
    window.setTimeout(() => hydrateLive(false), 0);
  }

  [
    elements.category,
    elements.location,
    elements.source,
    elements.fit,
    elements.age,
    elements.sort,
    elements.researchOnly,
    elements.entryOnly,
    elements.newOnly,
  ].forEach((element) => element.addEventListener("change", () => applyFilters(true)));
  elements.search.addEventListener("input", () => applyFilters(true));
  elements.clear.addEventListener("click", resetFilters);
  elements.emptyClear.addEventListener("click", resetFilters);
  elements.export.addEventListener("click", exportFiltered);
  elements.refreshLive.addEventListener("click", () => hydrateLive(true));
  elements.allView.addEventListener("click", () => { state.view = "all"; applyFilters(true); });
  elements.savedView.addEventListener("click", () => { state.view = "saved"; applyFilters(true); });
  elements.copyEmail.addEventListener("click", copyEmail);
  elements.loadMore.addEventListener("click", () => {
    state.displayLimit += PAGE_SIZE;
    applyFilters(false);
  });

  $$('[data-close-dialog]').forEach((button) => {
    button.addEventListener("click", () => $(`#${button.dataset.closeDialog}`)?.close());
  });
  [elements.detailsDialog, elements.emailDialog].forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });

  initialize();
})();
