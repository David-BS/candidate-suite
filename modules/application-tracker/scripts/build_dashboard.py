"""
Generates the HTML of an interactive application-tracking dashboard from a CSV
(or from direct JSON data).

The produced HTML is a FRAGMENT (no <html>/<head>/<body>) meant to be displayed
via the inline visualization tool. It includes:
- counters (total, by status, recent)
- 2 donuts (by language, by status) via Chart.js
- a sortable (click on header) and filterable (status, language, search) table
- BATCH status editing: a per-row dropdown, local accumulation, a
  "Save (N)" button that sends ONE grouped sendPrompt

Read-only mode (--readonly): no status editing, no Save button
(used for the ephemeral mode, with no file to persist to).

Localization (surface contract, LNG-2 S2 — option B):
- The HTML structure, the sendPrompt directives and the print() output are
  ENGLISH-CANONICAL (machine/Claude-facing), never localized.
- The VISIBLE labels default to English (LABELS_EN) and are localized by the
  model through --labels-json (interface language). When --labels-json is given
  it must carry the EXACT key set (anti-drift), otherwise English is used.
- Statuses are stored ENGLISH-CANONICAL (engine, cf. 0.11.0); only their DISPLAY
  text is localized via the status_* labels — the <select>/<option> values stay
  canonical so the engine and the sendPrompt keep speaking canonical English.
- This surface carries NO interface-language selector (option B): the language is
  set by the model via --labels-json, and the memory-preference precedence
  propagates it. The switching affordance lives on the entry selection widget.

Usage:
    python build_dashboard.py --input-path suivi.csv --output-path dashboard.html
    python build_dashboard.py --data-json '[{...}]' --output-path dashboard.html
    python build_dashboard.py --input-path suivi.csv --readonly --output-path dash.html

The resulting HTML is written to --output-path; Claude reads it and passes it to
the visualization tool. The available statuses can be passed via --statuses
(comma-separated); default: standard list.
"""

import argparse
import csv
import io
import json
import sys
from pathlib import Path


FIELDNAMES = [
    "date",
    "company",
    "position",
    "language",
    "status",
    "deliverables",
    "conversation",
    "title",
    "notes",
]

DEFAULT_STATUSES = [
    "Applied",
    "Interview scheduled",
    "In progress",
    "Offer",
    "Rejected",
    "Withdrawn",
]

# Canonical status -> LABELS_EN key. Display localization only: the stored/engine
# value stays the canonical English string; statusLabel() maps it to the visible
# text. A custom status (not among the 6) falls back to its raw stored string.
STATUS_LABEL_KEYS = {
    "Applied": "status_applied",
    "Interview scheduled": "status_interview_scheduled",
    "In progress": "status_in_progress",
    "Offer": "status_offer",
    "Rejected": "status_rejected",
    "Withdrawn": "status_withdrawn",
}

# English-canonical visible labels. --labels-json overrides this with the
# interface-language strings (exact same key set).
LABELS_EN = {
    "dashboard_aria": "Application-tracking dashboard, with filters, sorting and status editing.",
    "guide_button": "Usage guide",
    "guide_button_title": "Show the tracker usage guide",
    "refresh_button": "Refresh from conversations",
    "refresh_button_title": "Rebuild the tracker from a fresh scan of the project's conversations",
    "chart_by_language": "By language",
    "chart_by_language_aria": "Breakdown of applications by language",
    "chart_by_status": "By status",
    "chart_by_status_aria": "Breakdown of applications by status",
    "search_placeholder": "Search…",
    "search_aria": "Search the applications",
    "filter_status_aria": "Filter by status",
    "filter_status_all": "All statuses",
    "filter_lang_aria": "Filter by language",
    "filter_lang_all": "All languages",
    "save_button": "Save \u2197",
    "discard_button": "Cancel",
    "save_count": "pending change(s)",
    "col_date": "Date",
    "col_company": "Company",
    "col_position": "Position",
    "col_language": "Lang",
    "col_status": "Status",
    "col_link": "Link",
    "empty_message": "No application matches the filters.",
    "legend_link_column": "Link column:",
    "legend_current": "current, to be linked at Refresh",
    "legend_linked": "linked (clickable on web)",
    "legend_deleted": "deleted",
    "legend_desktop_example": "date - company - position",
    "legend_desktop_text": "marker to find in the sidebar",
    "legend_web_clickable": "clickable link",
    "conv_deleted_title": "Deleted conversation \u2014 link invalidated",
    "conv_desktop_title": "Marker to find (or copy) in the sidebar",
    "conv_current_title": "Produced in the current conversation \u2014 link to be set at the next Refresh",
    "conv_unlinked_title": "Link to be set at the next Refresh",
    "conv_link_fallback": "link",
    "counter_total": "Total",
    "counter_applied": "Applied",
    "counter_interview": "Interview",
    "counter_offer": "Offer",
    "status_applied": "Applied",
    "status_interview_scheduled": "Interview scheduled",
    "status_in_progress": "In progress",
    "status_offer": "Offer",
    "status_rejected": "Rejected",
    "status_withdrawn": "Withdrawn",
}


def parse_csv(text):
    entries = []
    if not text or not text.strip():
        return entries
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        entries.append({f: (row.get(f, "") or "").strip() for f in FIELDNAMES})
    return entries


def build_html(entries, statuses, readonly, surface, ui_lang, labels):
    """Builds the dashboard's HTML fragment."""
    data_json = json.dumps(entries, ensure_ascii=False)
    statuses_json = json.dumps(statuses, ensure_ascii=False)
    readonly_js = "true" if readonly else "false"
    labels_json = json.dumps(labels, ensure_ascii=False)
    # Status DISPLAY map: canonical -> localized label (values stay canonical).
    status_labels = {
        canon: labels.get(key, canon) for canon, key in STATUS_LABEL_KEYS.items()
    }
    status_labels_json = json.dumps(status_labels, ensure_ascii=False)

    # NB: no f-string for the big block (too many JS braces). We use
    # markers replaced afterwards.
    html = r"""<div style="padding: 1rem 0;">
<h2 id="srTitle" class="sr-only"></h2>

<div style="display:flex; justify-content:flex-end; gap:8px; margin-bottom:12px; flex-wrap:wrap;">
  <button id="guideBtn" type="button" style="font-size:12px; padding:5px 10px; border:0.5px solid var(--color-border-secondary); border-radius:var(--border-radius-md); background:var(--color-background-primary); color:var(--color-text-secondary); cursor:pointer;"></button>
  <button id="refreshBtn" type="button" style="font-size:12px; padding:5px 10px; border:0.5px solid var(--color-border-secondary); border-radius:var(--border-radius-md); background:var(--color-background-primary); color:var(--color-text-secondary); cursor:pointer;"></button>
</div>

<div id="counters" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 1.5rem;"></div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 1.5rem;">
  <div>
    <p id="langChartTitle" style="font-size: 13px; color: var(--color-text-secondary); margin: 0 0 8px;"></p>
    <div style="position: relative; height: 150px;">
      <canvas id="langChart" role="img"></canvas>
    </div>
  </div>
  <div>
    <p id="statusChartTitle" style="font-size: 13px; color: var(--color-text-secondary); margin: 0 0 8px;"></p>
    <div style="position: relative; height: 150px;">
      <canvas id="statusChart" role="img"></canvas>
    </div>
  </div>
</div>

<div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 12px;">
  <input type="text" id="search" style="flex: 1; min-width: 140px;" />
  <select id="filterStatus"><option value=""></option></select>
  <select id="filterLang"><option value=""></option></select>
</div>

<div id="saveBar" style="display: none; align-items: center; gap: 12px; margin-bottom: 12px; padding: 10px 12px; background: var(--color-background-info); border-radius: var(--border-radius-md);">
  <span id="saveCount" style="font-size: 13px; color: var(--color-text-info);"></span>
  <button id="saveBtn" style="margin-left: auto;"></button>
  <button id="discardBtn"></button>
</div>

<div style="background: var(--color-background-primary); border-radius: var(--border-radius-lg); border: 0.5px solid var(--color-border-tertiary); overflow-x: auto;">
  <table id="tbl" style="width: 100%; font-size: 13px; border-collapse: collapse; min-width: 560px;">
    <thead>
      <tr id="headRow" style="border-bottom: 0.5px solid var(--color-border-tertiary);"></tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<p id="emptyMsg" style="display:none; font-size:13px; color: var(--color-text-secondary); padding: 16px 4px;"></p>
<div id="convLegend" style="display:none; font-size:11px; color: var(--color-text-secondary); margin-top:10px; gap:16px; flex-wrap:wrap; align-items:center;">
  <span id="legLinkColumn" style="color: var(--color-text-tertiary);"></span>
  <span id="legLink"></span>
  <span id="legCurrent"></span>
  <span id="legLinked"></span>
  <span id="legDeleted"></span>
</div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
(function(){
  var DATA = __DATA__;
  var STATUSES = __STATUSES__;
  var READONLY = __READONLY__;
  var L = __LABELS__;
  var STATUS_LABELS = __STATUS_LABELS__;
  __SURFACE_OVERRIDE__

  // Surface detection: the desktop app exposes "Electron"/"Claude" in the userAgent.
  // On desktop, an https link opens the browser (bad) → we render text;
  // on web, the https link opens the conversation (new tab, same account) → we render a link.
  // window.__SURFACE__ ("desktop"/"web") lets you force the rendering (tests, preference).
  var IS_DESKTOP = (window.__SURFACE__ === "desktop") ||
                   (window.__SURFACE__ !== "web" && /electron|\bclaude\b/i.test(navigator.userAgent || ""));

  // Displayed label for a canonical status (values stay canonical everywhere).
  function statusLabel(s){ return (STATUS_LABELS && STATUS_LABELS[s]) || s; }

  // Builds the web URL of a conversation from a token (bare UUID or full URL).
  function convUrl(token){
    token = (token || "").trim();
    if (!token) return "";
    if (/^https?:\/\//i.test(token)) return token;
    if (/^[0-9a-f-]{8,}$/i.test(token)) return "https://claude.ai/chat/" + token;
    return "";
  }

  var pending = {};            // key -> new status (pending changes)
  var sortCol = "date";
  var sortDir = -1;            // -1 descending, 1 ascending
  var langChart = null, statusChart = null;

  // ---- DISPLAY-PREFERENCES cache (DRV-8) ----
  // window.storage = UI cache ONLY (sort, filters). NEVER the business
  // data: applications live in the project CSV (source of truth,
  // read by manage_tracker.py). If the cache and the CSV diverge, the CSV wins.
  // Everything degrades cleanly when window.storage is absent (ephemeral mode,
  // preview outside the app): defaults apply, no error.
  // Key < 200 chars, no space/separator/quote. Value = serialized JSON.
  // shared:false implied (preferences private to the user).
  var UIPREFS_KEY = "candidate-suite:dashboard:ui-prefs";
  var uiPrefsReady = false;    // true once the initial read is done

  function uiStorageAvailable(){
    return (typeof window !== "undefined") && !!window.storage;
  }

  // Reads the preferences at startup. get() THROWS if the key is absent
  // (does not return null) → try/catch required, absence is not an error.
  function loadUIPrefs(done){
    if (!uiStorageAvailable()){ done(null); return; }
    var p;
    try { p = window.storage.get(UIPREFS_KEY); }
    catch (e){ done(null); return; }
    Promise.resolve(p).then(function(res){
      if (res && res.value){
        try { done(JSON.parse(res.value)); }
        catch (e){ done(null); }
      } else { done(null); }
    }).catch(function(){ done(null); });
  }

  // Writes the current display state. Silent if unavailable; never blocking.
  // Does not write before the initial read (avoids overwriting the cache with defaults).
  function saveUIPrefs(){
    if (!uiPrefsReady || !uiStorageAvailable()) return;
    var prefs = {
      sortCol: sortCol,
      sortDir: sortDir,
      filterStatus: (document.getElementById("filterStatus") || {}).value || "",
      filterLang: (document.getElementById("filterLang") || {}).value || "",
      search: (document.getElementById("search") || {}).value || ""
    };
    try {
      var r = window.storage.set(UIPREFS_KEY, JSON.stringify(prefs));
      if (r && typeof r.catch === "function") r.catch(function(){});
    } catch (e){ /* best-effort cache: never block the UI */ }
  }

  // Applies the read preferences to the controls + sort variables.
  // Robustness: filter values that no longer match any option
  // (status/language gone from the CSV) are ignored by the <select> (stays "").
  function applyUIPrefs(prefs){
    if (!prefs) return;
    if (typeof prefs.sortCol === "string") sortCol = prefs.sortCol;
    if (prefs.sortDir === 1 || prefs.sortDir === -1) sortDir = prefs.sortDir;
    var fs = document.getElementById("filterStatus");
    var fl = document.getElementById("filterLang");
    var se = document.getElementById("search");
    if (fs && typeof prefs.filterStatus === "string") fs.value = prefs.filterStatus;
    if (fl && typeof prefs.filterLang === "string") fl.value = prefs.filterLang;
    if (se && typeof prefs.search === "string") se.value = prefs.search;
  }

  function keyOf(e){ return [e.company, e.position].join("||"); }

  // "Lost" row: at least one ✗ marker (deleted) AND no live marker left
  // (neither active link → uuid, nor ◆ current). We then grey the whole row's background.
  function isRowDeleted(c){
    if(!c) return false;
    var parts = String(c).split(";").map(function(x){ return x.trim(); }).filter(Boolean);
    if(!parts.length) return false;
    var anyDeleted = false, anyLiving = false;
    parts.forEach(function(p){
      if(/\u2717/.test(p)) anyDeleted = true;
      else if(p.indexOf("\u2192") > -1 || /\u25C6/.test(p)) anyLiving = true;
    });
    return anyDeleted && !anyLiving;
  }

  function esc(s){
    s = (s == null ? "" : String(s));
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  // Link column: the conversation is multi-valued ("label → url" separated by " ; ").
  // Each entry becomes a distinct dated link (text = date without the year, title = full label).
  // DRV-5: on desktop we show the marker to find in the sidebar. We
  // prefer the REAL title captured at scan (`realTitle`, robust if the user has
  // not renamed); only as a fallback do we revert to the fabricated marker `📋 …`.
  function renderConv(c, company, position, realTitle){
    if(!c) return "";
    var parts = String(c).split(";").map(function(x){ return x.trim(); }).filter(Boolean);
    return parts.map(function(p){
      var arrow = p.indexOf("\u2192"); // →
      var deleted = /\u2717/.test(p);
      var here = /\u25C6/.test(p);
      var rawLabel = (arrow > -1 ? p.slice(0, arrow) : p)
                       .replace(/\u2717/g, "")
                       .replace(/\u25C6/g, "")
                       .trim();
      var token = (arrow > -1) ? p.slice(arrow + 1).trim() : "";
      var url = convUrl(token) || (/^https?:\/\//i.test(p) ? p.trim() : "");
      var dm = rawLabel.match(/(\d{4})-(\d{2})-(\d{2})/);
      var dateShort = dm ? (dm[2] + "-" + dm[3]) : (rawLabel || L.conv_link_fallback);
      var fullDate = dm ? dm[0] : rawLabel;
      // Marker to find/copy in the sidebar: real title if captured,
      // otherwise the fabricated marker `📋 date - company - position`.
      var fabricated = "\ud83d\udccb " + fullDate +
                       (company ? " - " + company : "") +
                       (position ? " - " + position : "");
      var marker = (realTitle && realTitle.trim()) ? realTitle.trim() : fabricated;

      // 1) Deleted conversation: URL invalidated → grey italic, not clickable
      if (deleted){
        return '<span title="'+esc(L.conv_deleted_title)+'" style="color:var(--color-text-tertiary); font-style:italic; white-space:nowrap;">'+esc(dateShort)+'</span>';
      }
      // 2) Existing conversation (known link)
      if (url){
        // Desktop: a link would open the browser → we show the exact marker to
        // find/copy in the sidebar (selectable with one click).
        if (IS_DESKTOP){
          return '<span title="'+esc(L.conv_desktop_title)+'" style="color:var(--color-text-secondary); user-select:all; -webkit-user-select:all; cursor:text;">'+esc(marker)+'</span>';
        }
        // Web: clickable link (new tab, same account).
        return '<a href="'+esc(url)+'" target="_blank" rel="noopener" title="'+esc(rawLabel||url)+'" style="color:var(--color-text-info); white-space:nowrap; text-decoration:none;">'+esc(dateShort)+'</a>';
      }
      // 3) Current conversation / not yet linked → grey, ◆ suffix
      var title3 = here ? L.conv_current_title : L.conv_unlinked_title;
      return '<span title="'+esc(title3)+'" style="color:var(--color-text-tertiary); white-space:nowrap;">'+esc(dateShort + (here ? "\u2009\u25C6" : ""))+'</span>';
    }).join(' <span style="color:var(--color-text-tertiary);">\u00b7</span> ');
  }

  function effectiveStatus(e){
    var k = keyOf(e);
    return (k in pending) ? pending[k] : (e.status || "Applied");
  }

  function uniq(arr){ return arr.filter(function(v,i){ return arr.indexOf(v)===i; }); }

  // ---- Static labels (from the interface-language label set) ----
  document.getElementById("srTitle").textContent = L.dashboard_aria;
  var gBtn = document.getElementById("guideBtn");
  gBtn.textContent = L.guide_button; gBtn.title = L.guide_button_title;
  var rBtn = document.getElementById("refreshBtn");
  rBtn.textContent = "\u21bb " + L.refresh_button; rBtn.title = L.refresh_button_title;
  document.getElementById("langChartTitle").textContent = L.chart_by_language;
  document.getElementById("statusChartTitle").textContent = L.chart_by_status;
  document.getElementById("langChart").setAttribute("aria-label", L.chart_by_language_aria);
  document.getElementById("statusChart").setAttribute("aria-label", L.chart_by_status_aria);
  var searchEl = document.getElementById("search");
  searchEl.placeholder = L.search_placeholder; searchEl.setAttribute("aria-label", L.search_aria);
  var fsEl = document.getElementById("filterStatus");
  fsEl.setAttribute("aria-label", L.filter_status_aria);
  fsEl.querySelector('option[value=""]').textContent = L.filter_status_all;
  var flEl = document.getElementById("filterLang");
  flEl.setAttribute("aria-label", L.filter_lang_aria);
  flEl.querySelector('option[value=""]').textContent = L.filter_lang_all;
  document.getElementById("emptyMsg").textContent = L.empty_message;
  if (!READONLY){
    document.getElementById("saveBtn").textContent = L.save_button;
    document.getElementById("discardBtn").textContent = L.discard_button;
  }

  // ---- Link-column legend (surface-aware) ----
  function buildLegend(){
    document.getElementById("legLinkColumn").textContent = L.legend_link_column;
    var legLink = document.getElementById("legLink");
    legLink.innerHTML = IS_DESKTOP
      ? '<span style="color: var(--color-text-secondary);">\ud83d\udccb '+esc(L.legend_desktop_example)+'</span>\u2003'+esc(L.legend_desktop_text)
      : '<span style="color: var(--color-text-info);">05-28</span>\u2003'+esc(L.legend_web_clickable);
    document.getElementById("legCurrent").innerHTML =
      '<span style="color: var(--color-text-tertiary);">05-29\u2009\u25C6</span>\u2003'+esc(L.legend_current);
    document.getElementById("legLinked").innerHTML =
      '<span style="color: var(--color-text-info);">05-29</span>\u2003'+esc(L.legend_linked);
    document.getElementById("legDeleted").innerHTML =
      '<span style="color: var(--color-text-tertiary); font-style:italic;">05-30\u2009\u2717</span>\u2003'+esc(L.legend_deleted);
  }

  // ---- Filters: populating the selects ----
  function populateFilters(){
    var fs = document.getElementById("filterStatus");
    var fl = document.getElementById("filterLang");
    var langs = uniq(DATA.map(function(e){ return e.language; }).filter(Boolean));
    STATUSES.forEach(function(s){
      var o = document.createElement("option"); o.value = s; o.textContent = statusLabel(s); fs.appendChild(o);
    });
    langs.forEach(function(l){
      var o = document.createElement("option"); o.value = l; o.textContent = l; fl.appendChild(o);
    });
  }

  function currentRows(){
    var q = (document.getElementById("search").value || "").toLowerCase();
    var fst = document.getElementById("filterStatus").value;
    var fl = document.getElementById("filterLang").value;
    var rows = DATA.filter(function(e){
      if (fst && effectiveStatus(e) !== fst) return false;
      if (fl && e.language !== fl) return false;
      if (q){
        var hay = (e.company+" "+e.position+" "+e.notes+" "+e.deliverables).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
    rows.sort(function(a,b){
      var va = (a[sortCol]||""), vb = (b[sortCol]||"");
      if (sortCol === "status"){ va = effectiveStatus(a); vb = effectiveStatus(b); }
      if (va < vb) return -1*sortDir;
      if (va > vb) return 1*sortDir;
      return 0;
    });
    return rows;
  }

  // ---- Counters ----
  function renderCounters(){
    var total = DATA.length;
    var counts = {};
    DATA.forEach(function(e){ var s = effectiveStatus(e); counts[s] = (counts[s]||0)+1; });
    var interview = 0;
    Object.keys(counts).forEach(function(s){
      if (s.toLowerCase().indexOf("interview")>-1) interview += counts[s];
    });
    var offers = counts["Offer"] || 0;
    var cards = [
      [L.counter_total, total],
      [L.counter_applied, counts["Applied"]||0],
      [L.counter_interview, interview],
      [L.counter_offer, offers]
    ];
    var html = cards.map(function(c){
      return '<div style="background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 1rem;">'+
        '<p style="font-size:13px; color: var(--color-text-secondary); margin:0 0 4px;">'+esc(c[0])+'</p>'+
        '<p style="font-size:24px; font-weight:500; margin:0;">'+c[1]+'</p></div>';
    }).join("");
    document.getElementById("counters").innerHTML = html;
  }

  // ---- Table ----
  var COLS = [
    ["date", L.col_date], ["company", L.col_company], ["position", L.col_position],
    ["language", L.col_language], ["status", L.col_status]
  ];

  function renderHead(){
    var tr = document.getElementById("headRow");
    tr.innerHTML = "";
    COLS.forEach(function(c){
      var th = document.createElement("th");
      th.style.cssText = "text-align:left; padding:10px 12px; font-weight:500; color: var(--color-text-secondary); cursor:pointer; white-space:nowrap;";
      var arrow = (sortCol===c[0]) ? (sortDir===1 ? " ↑" : " ↓") : "";
      th.textContent = c[1] + arrow;
      th.onclick = function(){
        if (sortCol === c[0]) sortDir = -sortDir; else { sortCol = c[0]; sortDir = 1; }
        saveUIPrefs();
        render();
      };
      tr.appendChild(th);
    });
    if (DATA.some(function(e){ return e.conversation; })){
      var th = document.createElement("th");
      th.style.cssText = "text-align:left; padding:10px 12px; font-weight:500; color: var(--color-text-secondary);";
      th.textContent = L.col_link;
      tr.appendChild(th);
    }
  }

  function statusPill(s){
    var info = (s.toLowerCase().indexOf("interview")>-1) || s==="Offer";
    var bg = info ? "var(--color-background-info)" : "var(--color-background-secondary)";
    var col = info ? "var(--color-text-info)" : "var(--color-text-secondary)";
    return '<span style="background:'+bg+'; color:'+col+'; font-size:12px; padding:3px 8px; border-radius: var(--border-radius-md); white-space:nowrap;">'+esc(statusLabel(s))+'</span>';
  }

  function render(){
    renderHead();
    renderCounters();
    renderCharts();
    var rows = currentRows();
    var tbody = document.getElementById("tbody");
    tbody.innerHTML = "";
    document.getElementById("emptyMsg").style.display = rows.length ? "none" : "block";
    var hasConv = DATA.some(function(e){ return e.conversation; });
    document.getElementById("convLegend").style.display = hasConv ? "flex" : "none";

    rows.forEach(function(e){
      var tr = document.createElement("tr");
      tr.style.borderBottom = "0.5px solid var(--color-border-tertiary)";
      if (isRowDeleted(e.conversation)){
        // Application whose conversations are all deleted: greyed background
        // to spot it at a glance (sort/edit stay active).
        tr.style.background = "var(--color-background-secondary)";
      }
      var k = keyOf(e);
      var changed = (k in pending);

      function td(content, extra){
        var d = document.createElement("td");
        d.style.cssText = "padding:10px 12px; "+(extra||"");
        d.innerHTML = content;
        return d;
      }
      tr.appendChild(td(esc((e.date||"").replace(/^\d{4}-/,"")), "color: var(--color-text-secondary); white-space:nowrap;"));
      tr.appendChild(td(esc(e.company), "white-space:nowrap;"));
      tr.appendChild(td(esc(e.position), "max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"));
      tr.appendChild(td(esc(e.language)));

      // Status column: pill (readonly) or select (editing)
      var statusTd = document.createElement("td");
      statusTd.style.cssText = "padding:10px 12px;";
      if (READONLY){
        statusTd.innerHTML = statusPill(effectiveStatus(e));
      } else {
        var sel = document.createElement("select");
        sel.style.cssText = "font-size:12px; padding:2px 6px; min-width:120px;"+(changed ? " border-color: var(--color-border-info);" : "");
        STATUSES.forEach(function(s){
          var o = document.createElement("option"); o.value = s; o.textContent = statusLabel(s);
          if (effectiveStatus(e) === s) o.selected = true;
          sel.appendChild(o);
        });
        sel.onchange = function(){
          var orig = e.status || "Applied";
          if (sel.value === orig){ delete pending[k]; }
          else { pending[k] = sel.value; }
          renderSaveBar();
          renderCounters(); renderCharts();
          sel.style.borderColor = (k in pending) ? "var(--color-border-info)" : "";
        };
        statusTd.appendChild(sel);
      }
      tr.appendChild(statusTd);

      if (hasConv){
        tr.appendChild(td(renderConv(e.conversation, e.company, e.position, e.title)));
      }
      tbody.appendChild(tr);
    });
  }

  // ---- Save bar (batch) ----
  function renderSaveBar(){
    if (READONLY) return;
    var n = Object.keys(pending).length;
    var bar = document.getElementById("saveBar");
    if (n === 0){ bar.style.display = "none"; return; }
    bar.style.display = "flex";
    document.getElementById("saveCount").textContent = n + " " + L.save_count;
  }

  function doSave(){
    var changes = Object.keys(pending).map(function(k){
      var parts = k.split("||");
      return { company: parts[0], position: parts[1], status: pending[k] };
    });
    var lines = changes.map(function(c){
      return "- " + c.company + " (" + c.position + ") \u2192 " + c.status;
    }).join("\n");
    // ENGLISH-CANONICAL directive (Claude-facing); statuses are canonical.
    var msg = "Update the application tracker with these status changes:\n" + lines;
    if (typeof sendPrompt === "function"){ sendPrompt(msg); }
  }

  // ---- Charts ----
  function renderCharts(){
    var isDark = matchMedia("(prefers-color-scheme: dark)").matches;
    var txt = isDark ? "#D3D1C7" : "#5F5E5A";

    var langCounts = {};
    DATA.forEach(function(e){ if(e.language){ langCounts[e.language]=(langCounts[e.language]||0)+1; } });
    var stCounts = {};
    DATA.forEach(function(e){ var s=effectiveStatus(e); stCounts[s]=(stCounts[s]||0)+1; });

    var palette = ["#378ADD","#1D9E75","#BA7517","#D85A30","#534AB7","#888780"];

    if (langChart) langChart.destroy();
    if (statusChart) statusChart.destroy();

    langChart = new Chart(document.getElementById("langChart"), {
      type: "doughnut",
      data: { labels: Object.keys(langCounts),
        datasets: [{ data: Object.values(langCounts),
          backgroundColor: ["#378ADD","#1D9E75","#BA7517"], borderWidth: 0 }] },
      options: { responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ position:"bottom", labels:{ color:txt, font:{size:12}, boxWidth:10, padding:10 } } } }
    });
    statusChart = new Chart(document.getElementById("statusChart"), {
      type: "doughnut",
      data: { labels: Object.keys(stCounts).map(statusLabel),
        datasets: [{ data: Object.values(stCounts), backgroundColor: palette, borderWidth: 0 }] },
      options: { responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ position:"bottom", labels:{ color:txt, font:{size:12}, boxWidth:10, padding:10 } } } }
    });
  }

  // ---- Init ----
  function init(){
    buildLegend();
    populateFilters();
    document.getElementById("search").oninput = function(){ saveUIPrefs(); render(); };
    document.getElementById("filterStatus").onchange = function(){ saveUIPrefs(); render(); };
    document.getElementById("filterLang").onchange = function(){ saveUIPrefs(); render(); };
    if (!READONLY){
      document.getElementById("saveBtn").onclick = doSave;
      document.getElementById("discardBtn").onclick = function(){ pending = {}; renderSaveBar(); render(); };
    }
    var gb = document.getElementById("guideBtn");
    if (gb) gb.onclick = function(){
      // ENGLISH-CANONICAL directive (Claude-facing), never localized.
      if (typeof sendPrompt === "function") sendPrompt("Show the usage guide for the application-tracking dashboard.");
    };
    var rb = document.getElementById("refreshBtn");
    if (rb) rb.onclick = function(){
      // ENGLISH-CANONICAL directive (Claude-facing), never localized.
      if (typeof sendPrompt === "function") sendPrompt("Rebuild the application tracker from a fresh scan of this project's conversations, merging with the current tracker \u2014 without overwriting my statuses or notes.");
    };
    // Display preferences (DRV-8): applied AFTER populateFilters (the
    // <option> elements must exist), BEFORE the first render. uiPrefsReady is set
    // in all cases (success, no cache, storage unavailable) so that
    // subsequent interactions persist. Asynchronous → render() in the callback.
    loadUIPrefs(function(prefs){
      applyUIPrefs(prefs);
      uiPrefsReady = true;
      render();
    });
  }

  if (typeof Chart === "undefined"){
    var iv = setInterval(function(){ if (typeof Chart !== "undefined"){ clearInterval(iv); init(); } }, 50);
  } else { init(); }
})();
</script>"""

    html = html.replace("__DATA__", data_json)
    html = html.replace("__STATUSES__", statuses_json)
    html = html.replace("__READONLY__", readonly_js)
    html = html.replace("__LABELS__", labels_json)
    html = html.replace("__STATUS_LABELS__", status_labels_json)
    # Surface override: "auto" leaves userAgent detection in place;
    # "desktop"/"web" forces rendering via the existing window.__SURFACE__ entry point.
    surface_js = "" if surface == "auto" else 'window.__SURFACE__ = "%s";' % surface
    html = html.replace("__SURFACE_OVERRIDE__", surface_js)
    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generates the tracking dashboard HTML"
    )
    parser.add_argument("--input-path", default="")
    parser.add_argument("--data-json", default="")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--readonly", action="store_true")
    parser.add_argument("--statuses", default="")
    parser.add_argument(
        "--surface",
        choices=["auto", "desktop", "web"],
        default="auto",
        help="Force link rendering: auto (userAgent detection), desktop (text), web (clickable links)",
    )
    parser.add_argument(
        "--ui-lang",
        default="en",
        help="Interface-language code (metadata; this surface has NO selector — option B). Labels themselves come from --labels-json.",
    )
    parser.add_argument(
        "--labels-json",
        default="",
        help="Optional. Visible labels in the interface language. If given, must carry the EXACT LABELS_EN key set.",
    )
    args = parser.parse_args()

    if args.data_json:
        try:
            entries = json.loads(args.data_json)
        except json.JSONDecodeError as e:
            print(f"\u274c Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        # normalize
        entries = [
            {f: str(d.get(f, "") or "").strip() for f in FIELDNAMES} for d in entries
        ]
    elif args.input_path and Path(args.input_path).exists():
        entries = parse_csv(Path(args.input_path).read_text(encoding="utf-8"))
    else:
        entries = []

    statuses = list(DEFAULT_STATUSES)
    if args.statuses:
        statuses = [s.strip() for s in args.statuses.split(",") if s.strip()]
    # ensure all statuses present in the data are in the list
    present = [e.get("status", "") for e in entries if e.get("status")]
    for s in present:
        if s not in statuses:
            statuses.append(s)

    # Resolve the visible labels: English-canonical base, overridden by
    # --labels-json (which must carry the exact key set — no half-localized UI).
    labels = dict(LABELS_EN)
    if args.labels_json:
        try:
            supplied = json.loads(args.labels_json)
        except json.JSONDecodeError as e:
            print(f"\u274c Invalid --labels-json: {e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(supplied, dict):
            print("\u274c --labels-json must be a JSON object.", file=sys.stderr)
            sys.exit(1)
        got, required = set(supplied), set(LABELS_EN)
        if got != required:
            print(
                f"\u274c Invalid labels — missing: {sorted(required - got)} ; extra: {sorted(got - required)}",
                file=sys.stderr,
            )
            sys.exit(1)
        labels = supplied

    html = build_html(
        entries, statuses, args.readonly, args.surface, args.ui_lang, labels
    )
    out = Path(args.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    mode = "read-only" if args.readonly else "editable"
    print(
        f"\u2705 Dashboard HTML generated ({mode}, {len(entries)} application(s)): {out}"
    )
    print(
        f"   - interface language: {args.ui_lang}{' (localized labels supplied)' if args.labels_json else ' (English default labels)'}"
    )


if __name__ == "__main__":
    main()
