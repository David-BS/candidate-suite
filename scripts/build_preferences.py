"""
Generates the HTML of the candidate-suite preferences panel.

The panel makes the configuration (candidate-config) VISIBLE and exposes two
persistence settings as action buttons that compose a directive prompt via
sendPrompt (the widget itself executes nothing):

- Signature : [No — this conversation] / [Yes — via a project]
- Tracker   : [Persistent — project file] / [Session view] / [View the guide]

The "Yes (project)" and "Persistent (project)" buttons trigger GUIDED FLOWS on
Claude's side (see modules/candidate-config/GUIDE.md). The "View the guide"
button launches the tabbed guide display (build_guide.py).
No more Google Drive option (removed in 0.4.2 — see roadmap, DRV cluster).

Localization (surface contract, LNG-2 S2 — option B):
- The HTML structure, the sendPrompt directives (PROMPTS) and the print() output
  are ENGLISH-CANONICAL (machine/Claude-facing), never localized.
- The VISIBLE labels default to English (LABELS_EN) and are localized by the
  model through --labels-json (interface language, EXACT key set — errors out on
  any missing/extra). This surface carries NO interface-language selector: the
  language is set by the model and propagated by the memory-preference precedence
  (interface language is not a candidate-config field — nothing is stored).

No value is hardcoded: profile and current state arrive as arguments
(agnosticity — see DEP-2).

The produced HTML is a FRAGMENT meant for the inline visualization tool.

Usage:
    python build_preferences.py --output-path panneau.html \\
        --config-json '[{"label":"Name","value":"…"},{"label":"Email","value":"…"}]' \\
        --sig-current project \\
        --tracker-current project \\
        --ui-lang fr \\
        --labels-json '{ …LABELS_EN key set, values in the interface language… }'

Parameters:
- config-json    : list of {label, value} shown read-only (profile + files).
                   Each item accepts two optional fields:
                     "badge"     → status pill (e.g. "present (project)",
                                   "referenced, missing", template source);
                     "badgeKind" → "ok" | "warn" | "muted" (pill color).
                   Filled by the orchestrator from resolve_files.py (the badge
                   text is supplied in the interface language by the model).
                   If omitted/empty → "configuration unavailable" notice.
- sig-current    : 'project' | 'session' | 'none' (default 'none') → "current" button.
- tracker-current: 'project' | 'session' | 'none' (default 'none') → "current" button.
                   project = persistent tracker (project file); session = ephemeral view.
- ui-lang        : interface-language code (metadata; no selector on this surface).
- labels-json    : optional; visible labels in the interface language. Exact key set.
"""

import argparse
import json
import sys
from pathlib import Path


# Prompts composed by each button (trigger the flows on Claude's side).
# ENGLISH-CANONICAL (Claude-facing), never localized.
PROMPTS = {
    "edit": (
        "Open my candidate-config configuration in edit mode to change my contact "
        "details (name, address, email, phone, LinkedIn) or my files (CV, templates)."
    ),
    "sig_no": (
        "For the signature: I'm not keeping it. Set my preference to "
        "'this conversation only' — I'll re-upload my image when I want a signed letter."
    ),
    "sig_yes": (
        "I want to keep my signature from one letter to the next. Walk me through it "
        "step by step: (1) how to create a project, (2) give me the exact text to paste "
        "so you turn my image into a reusable file, (3) explain how to place that file "
        "in the project files so it is used for every new letter."
    ),
    "track_project": (
        "I want persistent tracking of my applications, stored in the project files "
        "(no Google Drive). Walk me through: (1) if I don't have a project, how to "
        "create one; (2) set up the tracking file (a versioned CSV in the project) and "
        "explain the ritual — you present the file, I add it to the project, I delete "
        "the old version identified by its name."
    ),
    "track_session": (
        "For tracking: just a view of this session, without saving anything. Show me "
        "the dashboard built from the applications we have seen, with no persistence."
    ),
    "track_guide": (
        "Show me the tracker guide: where the tracking file lives (in the project "
        "files), what the dashboard is for, and how to update it (you regenerate the "
        "versioned CSV, I add it to the project, I delete the old one)."
    ),
}

# English-canonical visible labels. --labels-json overrides this with the
# interface-language strings (exact same key set).
LABELS_EN = {
    "panel_aria": "candidate-suite preferences: profile (read-only), the choice to keep your signature, and application-tracking options (project file).",
    "profile_heading": "Your profile",
    "edit_button": "Edit",
    "config_unavailable": "Configuration unavailable.",
    "sig_heading": "Keep your signature for your next letters?",
    "sig_no_label": "No",
    "sig_no_note": "this conversation only",
    "sig_yes_label": "Yes",
    "sig_yes_note": "a project is required",
    "tracker_heading": "Tracking your applications",
    "tracker_heading_note": "in the project files",
    "track_project_label": "Persistent tracking",
    "track_project_note": "file in the project",
    "track_session_label": "This session's view",
    "track_session_note": "without saving",
    "track_guide_label": "View the tracker guide",
    "current_tag": "current",
}


def build_html(config_items, sig_current, tracker_current, ui_lang, labels):
    data = {
        "config": config_items or [],
        "sigCurrent": sig_current,
        "trackerCurrent": tracker_current,
        "prompts": PROMPTS,
        "L": labels,
    }
    data_json = json.dumps(data, ensure_ascii=False)

    html = r"""<div style="padding: 1rem 0;">
<h2 id="srTitle" class="sr-only"></h2>

<div id="profileCard" style="background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 1rem 1.25rem; margin-bottom: 1.5rem;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px;">
    <span style="font-weight:500; font-size:14px;"><i class="ti ti-user" style="font-size:18px; vertical-align:-3px; margin-right:6px;" aria-hidden="true"></i><span id="profileHeading"></span></span>
    <button id="editBtn" style="font-size:12px; padding:5px 12px;"></button>
  </div>
  <table id="profileTable" style="width:100%; font-size:13px; table-layout:fixed;"></table>
</div>

<div style="margin-bottom: 1.5rem;">
  <div style="font-size:14px; font-weight:500; margin-bottom:8px;"><i class="ti ti-signature" style="font-size:18px; vertical-align:-3px; margin-right:6px;" aria-hidden="true"></i><span id="sigHeading"></span></div>
  <div style="display:flex; flex-direction:column; gap:8px;">
    <button class="act" data-act="sig_no" style="text-align:left; font-size:13px; padding:10px 14px;"></button>
    <button class="act" data-act="sig_yes" style="text-align:left; font-size:13px; padding:10px 14px;"></button>
  </div>
</div>

<div>
  <div style="font-size:14px; font-weight:500; margin-bottom:8px;"><i class="ti ti-folder" style="font-size:18px; vertical-align:-3px; margin-right:6px;" aria-hidden="true"></i><span id="trackerHeading"></span> <span id="trackerHeadingNote" style="color:var(--color-text-tertiary); font-weight:400;"></span></div>
  <div style="display:flex; flex-direction:column; gap:8px;">
    <button class="act" data-act="track_project" style="text-align:left; font-size:13px; padding:10px 14px;"><i class="ti ti-chart-bar" style="font-size:16px; vertical-align:-2px; margin-right:8px;" aria-hidden="true"></i><span class="actbody"></span></button>
    <button class="act" data-act="track_session" style="text-align:left; font-size:13px; padding:10px 14px;"><i class="ti ti-eye" style="font-size:16px; vertical-align:-2px; margin-right:8px;" aria-hidden="true"></i><span class="actbody"></span></button>
    <button class="act" data-act="track_guide" style="text-align:left; font-size:13px; padding:10px 14px;"><i class="ti ti-help" style="font-size:16px; vertical-align:-2px; margin-right:8px;" aria-hidden="true"></i><span class="actbody"></span></button>
  </div>
</div>
</div>

<script>
(function(){
  var D = __DATA__;
  var L = D.L;

  function esc(s){
    s = (s==null?"":String(s));
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  var ARROW = "\u2009\u2197"; // thin space + ↗, marks a button that leads to a guided flow

  // ---- Static labels (from the interface-language label set) ----
  document.getElementById("srTitle").textContent = L.panel_aria;
  document.getElementById("profileHeading").textContent = L.profile_heading;
  document.getElementById("editBtn").innerHTML = esc(L.edit_button) + ARROW;
  document.getElementById("sigHeading").textContent = L.sig_heading;
  document.getElementById("trackerHeading").textContent = L.tracker_heading;
  document.getElementById("trackerHeadingNote").textContent = "\u2014 " + L.tracker_heading_note;

  // Action buttons: bold label + grey note; ↗ on the ones that open a flow.
  function actHtml(label, note, arrow){
    return '<span style="font-weight:500;">'+esc(label)+'</span> <span style="color:var(--color-text-tertiary);">\u2014 '+esc(note)+(arrow?ARROW:"")+'</span>';
  }
  var SIG = {
    sig_no:  actHtml(L.sig_no_label,  L.sig_no_note,  false),
    sig_yes: actHtml(L.sig_yes_label, L.sig_yes_note, true)
  };
  document.querySelector('.act[data-act="sig_no"]').innerHTML  = SIG.sig_no;
  document.querySelector('.act[data-act="sig_yes"]').innerHTML = SIG.sig_yes;
  // Tracker action buttons keep their leading icon; the body span carries label + note.
  var TRACK = {
    track_project: actHtml(L.track_project_label, L.track_project_note, true),
    track_session: actHtml(L.track_session_label, L.track_session_note, true),
    track_guide:   '<span style="font-weight:500;">'+esc(L.track_guide_label)+'</span>'+ARROW
  };
  document.querySelector('.act[data-act="track_project"] .actbody').innerHTML = TRACK.track_project;
  document.querySelector('.act[data-act="track_session"] .actbody').innerHTML = TRACK.track_session;
  document.querySelector('.act[data-act="track_guide"] .actbody').innerHTML   = TRACK.track_guide;

  // ---- Profile table ----
  var tbl = document.getElementById("profileTable");
  function badgeHtml(c){
    if (!c.badge) return "";
    var col = "var(--color-text-tertiary)";
    if (c.badgeKind === "ok") col = "var(--color-text-info)";
    else if (c.badgeKind === "warn") col = "var(--color-text-secondary)";
    return ' <span style="font-size:11px; margin-left:8px; padding:1px 7px; border-radius:10px; border:0.5px solid var(--color-border-tertiary); color:'+col+'; white-space:nowrap;">'+esc(c.badge)+'</span>';
  }
  if (D.config && D.config.length){
    tbl.innerHTML = D.config.map(function(c){
      return '<tr><td style="color:var(--color-text-secondary); padding:4px 0; width:120px; vertical-align:top;">'+esc(c.label)+'</td>'
           + '<td style="padding:4px 0; overflow:hidden; text-overflow:ellipsis;">'+esc(c.value)+badgeHtml(c)+'</td></tr>';
    }).join("");
  } else {
    tbl.innerHTML = '<tr><td style="color:var(--color-text-tertiary); padding:4px 0;">'+esc(L.config_unavailable)+'</td></tr>';
  }

  // ---- "current" markers + button wiring ----
  var curMap = {
    sig_no: D.sigCurrent === "session",
    sig_yes: D.sigCurrent === "project",
    track_project: D.trackerCurrent === "project",
    track_session: D.trackerCurrent === "session"
  };
  document.querySelectorAll(".act").forEach(function(b){
    if (curMap[b.dataset.act]){
      b.style.border = "2px solid var(--color-border-info)";
      b.insertAdjacentHTML("beforeend", ' <span style="font-size:11px; color:var(--color-text-info);">\u00b7 '+esc(L.current_tag)+'</span>');
    }
    b.addEventListener("click", function(){
      var m = D.prompts[b.dataset.act];
      if (m && typeof sendPrompt === "function"){ sendPrompt(m); }
    });
  });

  document.getElementById("editBtn").onclick = function(){
    if (typeof sendPrompt === "function"){ sendPrompt(D.prompts.edit); }
  };
})();
</script>"""

    return html.replace("__DATA__", data_json)


def main():
    parser = argparse.ArgumentParser(description="Generates the preferences panel")
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--config-json", default="")
    parser.add_argument("--sig-current", default="none", choices=["project", "session", "none"])
    parser.add_argument("--tracker-current", default="none", choices=["project", "session", "none"])
    parser.add_argument("--ui-lang", default="en",
                        help="Interface-language code (metadata; this surface has NO selector — option B). Labels come from --labels-json.")
    parser.add_argument("--labels-json", default="",
                        help="Optional. Visible labels in the interface language. If given, must carry the EXACT LABELS_EN key set.")
    args = parser.parse_args()

    config_items = []
    if args.config_json:
        try:
            config_items = json.loads(args.config_json)
        except json.JSONDecodeError as e:
            print(f"\u274c Invalid config-json: {e}", file=sys.stderr)
            sys.exit(1)

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
            print(f"\u274c Invalid labels — missing: {sorted(required - got)} ; extra: {sorted(got - required)}", file=sys.stderr)
            sys.exit(1)
        labels = supplied

    html = build_html(config_items, args.sig_current, args.tracker_current, args.ui_lang, labels)
    out = Path(args.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"\u2705 Preferences panel generated: {out}")
    print(f"   - {len(config_items)} profile row(s); signature='{args.sig_current}'; tracker='{args.tracker_current}'")
    print(f"   - interface language: {args.ui_lang}{' (localized labels supplied)' if args.labels_json else ' (English default labels)'}")


if __name__ == "__main__":
    main()
