"""
Generates the HTML of the tracker usage guide (3 tabs):
  1. The tracking file (timestamped versioned CSV, kept in the PROJECT files) —
     includes an HTML reconstruction of the "Add to project" menu (right-aligned),
     with no raster image: crisp, lightweight and portable rendering.
  2. The dashboard (overview + description of fields and buttons)
  3. Your documents ("conversation = archive" — no more Drive folder)

Reflects the 0.4.2 model: no more Google Drive. The tracker is a timestamp-
versioned project file (unique names); updating it follows the roadmap ritual
(the assistant regenerates → the user adds it to the project via the
"Copy ⌄" → "Add to project" menu → deletes the previous version spotted by its
name). Deliverable archiving is dropped: produced documents stay reachable as
download links in the conversation, found again via the tracker's "Link"
column (DRV-3).

Localization (surface contract, LNG-2 S2 — option B):
- The HTML structure and the print() output are ENGLISH-CANONICAL, never localized.
- The VISIBLE text defaults to English (LABELS_EN) and is localized by the model
  through --labels-json (interface language, EXACT key set — errors out on any
  missing/extra). Prose values may carry inline markup (<strong>, mono <span>):
  the model translates the text and PRESERVES the tags verbatim.
- This surface carries NO interface-language selector (option B) and no sendPrompt:
  it is read-only help. The language is set by the model and propagated by the
  memory-preference precedence.

Parameters (agnostic — nothing hardcoded):
- --candidate-name  : name shown in the examples (default "Candidate")
- --tracker-example : example name of the tracker file
                      (default "Applications_Tracker_YYYYMMDD_HHMM.csv")
- --ui-lang         : interface-language code (metadata; no selector on this surface)
- --labels-json     : optional; visible text in the interface language. Exact key set.

The produced HTML is a FRAGMENT meant for the inline visualization tool.

Usage:
    python build_guide.py --output-path guide.html --candidate-name "Jordan Lee-Carter"
"""

import argparse
import json
import sys
from pathlib import Path


# English-canonical visible text. --labels-json overrides this with the
# interface-language strings (exact same key set). Prose values keep their inline
# markup; the model translates the text and preserves the tags.
LABELS_EN = {
    "guide_aria": "Tracker guide in three tabs: the tracking file kept in the project, the dashboard with its buttons and fields, and where to find your documents (the conversation acts as the archive).",
    "tab_file": "The tracking file",
    "tab_dash": "The dashboard",
    "tab_docs": "Your documents",
    # --- File tab ---
    "file_intro": "Your applications are recorded in a file <strong style='font-weight:500;'>kept in your project files</strong> (no Google Drive). Its name contains the date and time:",
    "file_columns": "It holds one row per application: date, company, position, language, status, <strong style='font-weight:500;'>conversation link</strong>, notes.",
    "file_ritual": "On each update, the assistant <strong style='font-weight:500; color:var(--color-text-primary);'>regenerates a new dated version</strong> of the tracking file and presents it to you. You add it to the project using the <strong style='font-weight:500; color:var(--color-text-primary);'>menu at the top right</strong> of the file viewer (the <strong style='font-weight:500; color:var(--color-text-primary);'>\u201cCopy\u2009\u25be\u201d</strong> button) and choosing <strong style='font-weight:500; color:var(--color-text-primary);'>\u201cAdd to project\u201d</strong>. Then go to the project and <strong style='font-weight:500; color:var(--color-text-primary);'>delete the old version</strong>, spotted by its older timestamp in the name. Since names are unique, deleting the old one never touches the new one.",
    "menu_aria": "File viewer menu: a Copy button opening Download as CSV, Add to project (highlighted), Publish artifact.",
    "menu_copy": "Copy",
    "menu_download": "Download as CSV",
    "menu_add": "Add to project",
    "menu_publish": "Publish artifact",
    # --- Dashboard tab ---
    "dash_intro": "An interactive view built from the tracking file.",
    "dash_notpermanent": "<strong style='font-weight:500; color:var(--color-text-info);'>It does not stay on screen.</strong> To bring it up, just ask \u2014 for example <span style='font-family:var(--font-mono); background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:4px; padding:1px 6px; white-space:nowrap;'>Where do my applications stand?</span> or <span style='font-family:var(--font-mono); background:var(--color-background-primary); border:0.5px solid var(--color-border-tertiary); border-radius:4px; padding:1px 6px;'>Show my applications dashboard</span>.",
    "dash_preview_label": "Preview:",
    "ex_counter_total": "Total",
    "ex_counter_applied": "Applied",
    "ex_counter_interview": "Interview",
    "ex_counter_offer": "Offer",
    "ex_search": "Search\u2026",
    "ex_filter_status": "Status",
    "ex_filter_lang": "Language",
    "ex_col_date": "Date",
    "ex_col_company": "Company",
    "ex_col_position": "Position",
    "ex_col_lang": "Lg",
    "ex_col_status": "Status",
    "ex_col_link": "Link",
    "ex_pill_applied": "Applied",
    "ex_pill_interview": "Interview",
    "ex_savebar": "2 pending change(s)",
    "ex_save": "Save",
    "ex_cancel": "Cancel",
    "dash_status_default": "When an application is added, the tool sets the status to its default <strong style='font-weight:500; color:var(--color-text-primary);'>\u201cApplied\u201d</strong>. <strong style='font-weight:500; color:var(--color-text-primary);'>You alone can change it</strong> \u2014 the assistant never changes a status on its own. To update it: <strong style='font-weight:500; color:var(--color-text-primary);'>1.</strong> pick the new status from the row's menu; <strong style='font-weight:500; color:var(--color-text-primary);'>2.</strong> click <strong style='font-weight:500; color:var(--color-text-primary);'>Save</strong>; <strong style='font-weight:500; color:var(--color-text-primary);'>3.</strong> add to the project the <strong style='font-weight:500; color:var(--color-text-primary);'>new version of the tracking file</strong> that is then presented to you (and delete the old one).",
    "leg_counters_lead": "Counters",
    "leg_counters_desc": "totals by status, at the top.",
    "leg_filters_lead": "Search / Status / Language",
    "leg_filters_desc": "filter the list instantly.",
    "leg_headers_lead": "Column headers",
    "leg_headers_desc": "a click sorts (arrow \u2191/\u2193).",
    "leg_statusmenu_lead": "Status menu",
    "leg_statusmenu_desc": "the only way to change an application's state; row by row, on your terms.",
    "leg_save_lead": "Save",
    "leg_save_desc": "the assistant regenerates the tracking file with your changes and presents it; it is up to you to add it to the project (and delete the old one). Nothing is written for you.",
    "leg_link_lead": "Link",
    "leg_link_desc": "one or more dated conversations (by date); each reopens the one holding the documents produced that day.",
    # --- Documents tab ---
    "docs_heading": "How to find your deliverables",
    "docs_intro": "Produced documents (letters, summaries, cards\u2026) are <strong style='font-weight:500;'>not filed in a folder</strong>: they stay reachable as <strong style='font-weight:500;'>download links in the conversation</strong> where they were generated. <strong style='font-weight:500;'>The conversation acts as the archive</strong>, and the <strong style='font-weight:500;'>dashboard is the index that leads to it.</strong>",
    "docs_mock_trackrow": "Tracking row",
    "docs_mock_letter": "letter",
    "docs_mock_prep": "interview prep",
    "docs_mock_chosen": "The chosen conversation",
    "docs_followlink_lead": "Follow the tracker link",
    "docs_followlink_desc": "each row carries the link(s) to its conversation(s), labeled by date. An application can span several conversations: open the one holding the document you want.",
    "docs_nothing_lead": "Nothing to file",
    "docs_nothing_desc": "no document is copied elsewhere: no folder to manage or clean up.",
    "docs_tip_lead": "Tip \u2014 a deliverable that matters?",
    "docs_tip_desc": "Download it to your computer when it is generated: a local copy, independent of the conversation \u2014 zero-cost insurance.",
}


def build_html(candidate_name, tracker_example, ui_lang, labels):
    data = {
        "candidate": candidate_name,
        "trackerExample": tracker_example,
        "L": labels,
    }
    data_json = json.dumps(data, ensure_ascii=False)

    html = r"""<div style="padding: 1rem 0;">
<h2 id="srTitle" class="sr-only"></h2>

<div role="tablist" id="tabbar" style="display:flex; gap:4px; border-bottom:0.5px solid var(--color-border-tertiary); margin-bottom:1.25rem;">
  <button class="gtab" role="tab" data-tab="file" style="border:0; background:transparent; padding:10px 14px; font-size:13px; cursor:pointer; border-bottom:2px solid transparent;"><i class="ti ti-file" style="font-size:16px; vertical-align:-2px; margin-right:6px;" aria-hidden="true"></i><span data-lab="tab_file"></span></button>
  <button class="gtab" role="tab" data-tab="dash" style="border:0; background:transparent; padding:10px 14px; font-size:13px; cursor:pointer; border-bottom:2px solid transparent;"><i class="ti ti-layout-dashboard" style="font-size:16px; vertical-align:-2px; margin-right:6px;" aria-hidden="true"></i><span data-lab="tab_dash"></span></button>
  <button class="gtab" role="tab" data-tab="docs" style="border:0; background:transparent; padding:10px 14px; font-size:13px; cursor:pointer; border-bottom:2px solid transparent;"><i class="ti ti-messages" style="font-size:16px; vertical-align:-2px; margin-right:6px;" aria-hidden="true"></i><span data-lab="tab_docs"></span></button>
</div>

<div class="gpanel" data-panel="file" style="font-size:14px; line-height:1.7;">
  <p data-html="file_intro" style="margin:0 0 12px;"></p>
  <div id="texample" style="font-family:var(--font-mono); font-size:13px; background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:10px 12px; margin-bottom:14px; word-break:break-all;"></div>
  <p data-html="file_columns" style="margin:0 0 10px;"></p>
  <div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
    <div style="flex:1; min-width:230px; display:flex; gap:8px; align-items:flex-start; background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:10px 12px; font-size:13px; line-height:1.6;">
      <i class="ti ti-refresh" style="color:var(--color-text-info); font-size:16px; margin-top:2px; flex-shrink:0;" aria-hidden="true"></i>
      <span data-html="file_ritual" style="color:var(--color-text-secondary);"></span>
    </div>
    <div id="menuMock" style="width:240px; margin-left:auto; border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-md); overflow:hidden; background:var(--color-background-primary); font-size:12px;" role="img">
      <div style="display:flex; align-items:center; gap:8px; padding:6px 8px; border-bottom:0.5px solid var(--color-border-tertiary);">
        <i class="ti ti-table" style="color:var(--color-text-secondary); font-size:15px; margin-right:auto;" aria-hidden="true"></i>
        <span style="border:0.5px solid var(--color-border-tertiary); border-radius:5px; padding:2px 8px; color:var(--color-text-secondary);"><span data-lab="menu_copy"></span>&#8201;&#9662;</span>
      </div>
      <div style="padding:4px 0;">
        <div data-lab="menu_download" style="padding:6px 12px; color:var(--color-text-secondary);"></div>
        <div data-lab="menu_add" style="padding:6px 12px; background:var(--color-background-secondary); color:var(--color-text-primary); font-weight:500;"></div>
        <div data-lab="menu_publish" style="padding:6px 12px; color:var(--color-text-secondary);"></div>
      </div>
    </div>
  </div>
</div>

<div class="gpanel" data-panel="dash" style="font-size:14px; line-height:1.6;">
  <p data-html="dash_intro" style="margin:0 0 10px;"></p>
  <div style="display:flex; gap:8px; align-items:flex-start; background:var(--color-background-info); border-radius:var(--border-radius-md); padding:10px 12px; margin-bottom:14px; font-size:13px; line-height:1.6;">
    <i class="ti ti-info-circle" style="font-size:16px; color:var(--color-text-info); margin-top:1px; flex-shrink:0;" aria-hidden="true"></i>
    <div data-html="dash_notpermanent"></div>
  </div>
  <p data-html="dash_preview_label" style="margin:0 0 12px; color:var(--color-text-secondary);"></p>
  <div style="border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-lg); padding:14px; background:var(--color-background-primary); margin-bottom:14px;">
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:12px;">
      <div style="background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:8px;"><div data-lab="ex_counter_total" style="font-size:11px; color:var(--color-text-secondary);"></div><div style="font-size:20px; font-weight:500;">6</div></div>
      <div style="background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:8px;"><div data-lab="ex_counter_applied" style="font-size:11px; color:var(--color-text-secondary);"></div><div style="font-size:20px; font-weight:500;">4</div></div>
      <div style="background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:8px;"><div data-lab="ex_counter_interview" style="font-size:11px; color:var(--color-text-secondary);"></div><div style="font-size:20px; font-weight:500;">1</div></div>
      <div style="background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:8px;"><div data-lab="ex_counter_offer" style="font-size:11px; color:var(--color-text-secondary);"></div><div style="font-size:20px; font-weight:500;">0</div></div>
    </div>
    <div style="display:flex; gap:8px; margin-bottom:10px; flex-wrap:wrap;">
      <span style="flex:1; min-width:120px; border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-md); padding:6px 10px; font-size:12px; color:var(--color-text-tertiary);"><i class="ti ti-search" aria-hidden="true"></i> <span data-lab="ex_search"></span></span>
      <span style="border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-md); padding:6px 10px; font-size:12px; color:var(--color-text-secondary);"><span data-lab="ex_filter_status"></span> &#9662;</span>
      <span style="border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-md); padding:6px 10px; font-size:12px; color:var(--color-text-secondary);"><span data-lab="ex_filter_lang"></span> &#9662;</span>
    </div>
    <table style="width:100%; font-size:12px; border-collapse:collapse;">
      <tr style="color:var(--color-text-secondary); text-align:left;">
        <th style="padding:4px 6px; font-weight:400;"><span data-lab="ex_col_date"></span> &#8595;</th><th style="padding:4px 6px; font-weight:400;" data-lab="ex_col_company"></th><th style="padding:4px 6px; font-weight:400;" data-lab="ex_col_position"></th><th style="padding:4px 6px; font-weight:400;" data-lab="ex_col_lang"></th><th style="padding:4px 6px; font-weight:400;" data-lab="ex_col_status"></th><th style="padding:4px 6px; font-weight:400;" data-lab="ex_col_link"></th>
      </tr>
      <tr style="border-top:0.5px solid var(--color-border-tertiary);">
        <td style="padding:5px 6px;">2026-05-29</td><td style="padding:5px 6px;">Globex</td><td style="padding:5px 6px;">Solution Leader</td><td style="padding:5px 6px;">FR</td>
        <td style="padding:5px 6px;"><span style="border:0.5px solid var(--color-border-secondary); border-radius:4px; padding:2px 6px;"><span data-lab="ex_pill_applied"></span> &#9662;</span></td>
        <td style="padding:5px 6px; color:var(--color-text-info); white-space:nowrap;"><span title="2026-05-29"><i class="ti ti-external-link" aria-hidden="true"></i> 29/05</span></td>
      </tr>
      <tr style="border-top:0.5px solid var(--color-border-tertiary);">
        <td style="padding:5px 6px;">2026-05-28</td><td style="padding:5px 6px;">Acme Financial Group</td><td style="padding:5px 6px;">IT &amp; Ops</td><td style="padding:5px 6px;">EN</td>
        <td style="padding:5px 6px;"><span style="background:var(--color-background-info); color:var(--color-text-info); border-radius:4px; padding:2px 6px;"><span data-lab="ex_pill_interview"></span> &#9662;</span></td>
        <td style="padding:5px 6px; color:var(--color-text-info); white-space:nowrap;"><span title="2026-05-28"><i class="ti ti-external-link" aria-hidden="true"></i> 28/05</span> <span title="2026-05-30"><i class="ti ti-external-link" aria-hidden="true"></i> 30/05</span></td>
      </tr>
    </table>
    <div style="display:flex; align-items:center; gap:10px; margin-top:12px; background:var(--color-background-info); border-radius:var(--border-radius-md); padding:8px 10px; font-size:12px; color:var(--color-text-info);">
      <span data-lab="ex_savebar" style="flex:1;"></span>
      <span data-lab="ex_save" style="border:0.5px solid var(--color-text-info); border-radius:4px; padding:3px 10px;"></span>
      <span data-lab="ex_cancel" style="padding:3px 6px;"></span>
    </div>
  </div>
  <div style="display:flex; gap:8px; align-items:flex-start; background:var(--color-background-secondary); border-radius:var(--border-radius-md); padding:10px 12px; margin-bottom:14px; font-size:13px; line-height:1.6;">
    <i class="ti ti-edit" style="font-size:16px; color:var(--color-text-info); margin-top:1px; flex-shrink:0;" aria-hidden="true"></i>
    <div data-html="dash_status_default"></div>
  </div>
  <div id="dashLegend" style="font-size:13px; color:var(--color-text-secondary); line-height:1.7;"></div>
</div>

<div class="gpanel" data-panel="docs" style="font-size:14px; line-height:1.7;">
  <div style="font-size:15px; font-weight:500; margin-bottom:8px;"><i class="ti ti-search" style="font-size:17px; vertical-align:-2px; margin-right:6px;" aria-hidden="true"></i><span data-lab="docs_heading"></span></div>
  <p data-html="docs_intro" style="margin:0 0 12px;"></p>
  <div style="display:flex; align-items:stretch; gap:10px; margin-bottom:14px; flex-wrap:wrap;">
    <div style="flex:1; min-width:185px; border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-md); padding:12px; background:var(--color-background-secondary);">
      <div style="font-size:12px; color:var(--color-text-secondary); margin-bottom:6px;"><i class="ti ti-table" style="vertical-align:-2px; margin-right:5px;" aria-hidden="true"></i><span data-lab="docs_mock_trackrow"></span> &#8212; Acme Financial Group &#183; IT &amp; Ops</div>
      <div style="font-size:12px; color:var(--color-text-info); line-height:2;"><i class="ti ti-external-link" style="vertical-align:-2px;" aria-hidden="true"></i> 2026-05-28 &#8212; <span data-lab="docs_mock_letter"></span><br/><i class="ti ti-external-link" style="vertical-align:-2px;" aria-hidden="true"></i> 2026-05-30 &#8212; <span data-lab="docs_mock_prep"></span></div>
    </div>
    <div style="display:flex; align-items:center; color:var(--color-text-tertiary); font-size:20px;">&#8594;</div>
    <div style="flex:1; min-width:150px; border:0.5px solid var(--color-border-tertiary); border-radius:var(--border-radius-md); padding:12px; background:var(--color-background-primary);">
      <div style="font-size:12px; color:var(--color-text-secondary); margin-bottom:6px;"><i class="ti ti-message-2" style="vertical-align:-2px; margin-right:5px;" aria-hidden="true"></i><span data-lab="docs_mock_chosen"></span></div>
      <div style="font-size:13px; line-height:1.9;"><i class="ti ti-download" style="vertical-align:-2px; color:var(--color-text-info);" aria-hidden="true"></i> Cover_Letter&#8230;_EN.docx<br/><i class="ti ti-download" style="vertical-align:-2px; color:var(--color-text-info);" aria-hidden="true"></i> Application_Summary&#8230;.pdf</div>
    </div>
  </div>
  <div id="docsList" style="font-size:13px; color:var(--color-text-secondary); line-height:1.8;"></div>
</div>
</div>

<script>
(function(){
  var D = __DATA__;
  var L = D.L;
  document.getElementById("texample").textContent = D.trackerExample;
  document.getElementById("srTitle").textContent = L.guide_aria;
  document.getElementById("menuMock").setAttribute("aria-label", L.menu_aria);

  function esc(s){
    s = (s==null?"":String(s));
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  // Plain-text labels (translated, no markup).
  document.querySelectorAll("[data-lab]").forEach(function(el){
    el.textContent = L[el.getAttribute("data-lab")] || "";
  });
  // Prose blocks (translated text keeps its inline markup → innerHTML).
  document.querySelectorAll("[data-html]").forEach(function(el){
    el.innerHTML = L[el.getAttribute("data-html")] || "";
  });

  // Dashboard legend: lead (bold) + description, from label pairs.
  var legend = [
    ["leg_counters_lead","leg_counters_desc"],
    ["leg_filters_lead","leg_filters_desc"],
    ["leg_headers_lead","leg_headers_desc"],
    ["leg_statusmenu_lead","leg_statusmenu_desc"],
    ["leg_save_lead","leg_save_desc"],
    ["leg_link_lead","leg_link_desc"]
  ];
  document.getElementById("dashLegend").innerHTML = legend.map(function(p){
    return '<div><strong style="font-weight:500; color:var(--color-text-primary);">'+esc(L[p[0]])+'</strong> \u2014 '+esc(L[p[1]])+'</div>';
  }).join("");

  // Documents list: same lead + description pattern (last item is a tip box).
  var docsList = [
    ["docs_followlink_lead","docs_followlink_desc",false],
    ["docs_nothing_lead","docs_nothing_desc",false],
    ["docs_tip_lead","docs_tip_desc",true]
  ];
  document.getElementById("docsList").innerHTML = docsList.map(function(p){
    var lead = '<strong style="font-weight:500; color:var(--color-text-primary);">'
             + (p[2] ? '<i class="ti ti-bulb" style="vertical-align:-2px; margin-right:4px;" aria-hidden="true"></i>' : '')
             + esc(L[p[0]])+'</strong> \u2014 '+esc(L[p[1]]);
    var wrap = p[2] ? ' style="margin-top:8px; padding-top:8px; border-top:0.5px solid var(--color-border-tertiary);"' : '';
    return '<div'+wrap+'>'+lead+'</div>';
  }).join("");

  // Tabs
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".gtab"));
  var panels = Array.prototype.slice.call(document.querySelectorAll(".gpanel"));
  function show(name){
    panels.forEach(function(p){ p.style.display = (p.dataset.panel === name) ? "block" : "none"; });
    tabs.forEach(function(t){
      var on = t.dataset.tab === name;
      t.style.borderBottomColor = on ? "var(--color-border-info)" : "transparent";
      t.style.color = on ? "var(--color-text-info)" : "var(--color-text-secondary)";
      t.style.fontWeight = on ? "500" : "400";
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
  }
  tabs.forEach(function(t){ t.addEventListener("click", function(){ show(t.dataset.tab); }); });
  show("file");
})();
</script>"""

    return html.replace("__DATA__", data_json)


def main():
    parser = argparse.ArgumentParser(description="Generates the tracker guide (tabs)")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--candidate-name", default="Candidate")
    parser.add_argument(
        "--tracker-example", default="Applications_Tracker_YYYYMMDD_HHMM.csv"
    )
    parser.add_argument(
        "--ui-lang",
        default="en",
        help="Interface-language code (metadata; this surface has NO selector — option B). Text comes from --labels-json.",
    )
    parser.add_argument(
        "--labels-json",
        default="",
        help="Optional. Visible text in the interface language. If given, must carry the EXACT LABELS_EN key set.",
    )
    args = parser.parse_args()

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

    html = build_html(args.candidate_name, args.tracker_example, args.ui_lang, labels)
    out = Path(args.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"\u2705 Tracker guide generated: {out}")
    print(
        f"   - interface language: {args.ui_lang}{' (localized labels supplied)' if args.labels_json else ' (English default labels)'}"
    )


if __name__ == "__main__":
    main()
