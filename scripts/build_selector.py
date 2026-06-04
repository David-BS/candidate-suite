#!/usr/bin/env python3
"""Builds the application-tools SELECTION WIDGET (HTML) rendered inline in chat.

The widget shows:
- an interface-language selector (changing it re-renders the widget in that
  language — the deliverables language is governed separately, see SKILL.md);
- the known memory data (editable);
- the job-posting field;
- the list of deliverables (checkboxes);
- a conditional signature zone (cover letter);
- a "Generate" button that composes a directive prompt via sendPrompt.

Localization (surface contract):
- The HTML structure, the sendPrompt directive and the print() output are
  ENGLISH-CANONICAL (machine/Claude-facing), never localized.
- The VISIBLE labels default to English (LABELS_EN) and are localized by the
  model through --labels-json (interface language). When --labels-json is
  given it must carry the EXACT key set (anti-drift), otherwise English is used.

Usage:
    python build_selector.py --output-path W.html \\
        --memory-json '[{"id":"profile","label":"Profile","value":"…","editable":true}]' \\
        --memory-active true \\
        --signature-in-memory true \\
        --already-done-json '["strategic_playbook"]' \\
        --ui-lang fr \\
        --labels-json '{"offer_label":"Offre d\'emploi (texte ou lien)", …}'

- memory-json : memory elements (list of {id, label, value, editable}).
- memory-active : 'true'/'false' — is memory active?
- signature-in-memory : 'true'/'false' — is a signature available (project/upload)?
- already-done-json : ids of already-generated deliverables (pre-checked + grayed).
- ui-lang : current interface-language code, used to pre-select the dropdown
            (the model sets it = memory preference if any, else the conversation
            language). Default 'en'.
- labels-json : optional; visible labels in the interface language. Exact key set.
"""

import argparse
import json
import sys
from pathlib import Path


# Standard deliverables: id -> module. Visible label/desc come from LABELS_EN
# (key deliv_<id>_label / deliv_<id>_desc), localizable via --labels-json.
DELIVERABLES = [
    ("strategic_playbook", "strategic-playbook-generator"),
    ("application_summary", "application-summary-generator"),
    ("interview_prep", "interview-prep-generator"),
    ("cover_letter", "cover-letter-generator"),
    ("quick_reference", "quick-reference-generator"),
    ("add_to_tracker", "application-tracker"),
]

# Imposed generation order (passed to Claude via SKILL.md, no longer in the visible prompt)
GENERATION_ORDER = [
    "strategic_playbook",
    "application_summary",
    "interview_prep",
    "cover_letter",
    "quick_reference",
    "add_to_tracker",
]

# Claude's official INTERFACE languages, shown as endonyms (their own language),
# like the native Claude language menu. Single source of truth, shared by the
# surfaces. Source: support.claude.com "How to use Claude in your preferred
# language" (11 languages, checked 2026-06-04). Kept in sync with Anthropic by a
# CI/CD step at deployment (see roadmap DEP-3) — NEVER fetched at runtime.
UI_LANGUAGES = [
    ("en", "English"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("hi", "हिन्दी"),
    ("id", "Bahasa Indonesia"),
    ("it", "Italiano"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("pt-BR", "Português (Brasil)"),
    ("es-419", "Español (Latinoamérica)"),
    ("es-ES", "Español (España)"),
]

# English-canonical visible labels. --labels-json overrides this with the
# interface-language strings (exact same key set).
LABELS_EN = {
    "widget_aria": "Application-tools selector: choose the documents to generate, paste the job posting, and launch generation.",
    "ui_language_label": "Interface language",
    "ui_language_other": "Other… (ISO code)",
    "offer_label": "Job posting (text or link)",
    "offer_placeholder": "Paste the posting here, or leave empty if already provided in the conversation…",
    "documents_heading": "Documents to generate",
    "toggle_all_check": "Check all",
    "toggle_all_uncheck": "Uncheck all",
    "generate_button": "Generate",
    "hint_min_one": "Check at least one document.",
    "mem_paused": "Memory paused. The data used will be whatever is provided in this conversation.",
    "mem_header": "Known data used",
    "mem_header_note": "(non-exhaustive — editable below)",
    "mem_none": "No data in memory for this application.",
    "mem_save_option": "Save the changes to memory (otherwise: one-off use for this application)",
    "deliv_done_tag": "already generated",
    "sig_title": "Handwritten signature (cover letter)",
    "sig_found": "Signature found, will be used by default.",
    "sig_skip": "Do not use the saved signature for this letter",
    "sig_none": "No signature available. You can attach an image (PNG/JPG/GIF/BMP) to your next message; it will be used for this letter.",
    "sig_memorize": "Keep this signature for future applications",
    "sig_none_hint": "Without an attached image: the letter will be generated without a signature (you can sign by hand).",
    "sig_paused": "Memory paused. You can attach a signature image (PNG/JPG/GIF/BMP) to your next message, for this letter only (no saving possible).",
    "sig_paused_hint": "Without an attached image: the letter will be generated without a signature.",
    "deliv_strategic_playbook_label": "Strategic playbook",
    "deliv_strategic_playbook_desc": "Company context, pain points, positioning, questions",
    "deliv_application_summary_label": "Application summary",
    "deliv_application_summary_desc": "Strengths/weaknesses, 5-sentence pitch, talking points",
    "deliv_interview_prep_label": "Interview prep",
    "deliv_interview_prep_desc": "Q&A for screening + skills validation",
    "deliv_cover_letter_label": "Cover letter",
    "deliv_cover_letter_desc": "Personalized letter (.docx)",
    "deliv_quick_reference_label": "Reference card",
    "deliv_quick_reference_desc": "Condensed from the other documents (to print)",
    "deliv_add_to_tracker_label": "Add to tracker",
    "deliv_add_to_tracker_desc": "Record this application in the dashboard",
}


def build_html(
    memory_items, memory_active, signature_in_memory, already_done, ui_lang, labels
):
    L = labels
    data = {
        "deliverables": [
            {
                "id": d[0],
                "module": d[1],
                "label": L["deliv_%s_label" % d[0]],
                "desc": L["deliv_%s_desc" % d[0]],
                "en": LABELS_EN["deliv_%s_label" % d[0]],
            }
            for d in DELIVERABLES
        ],
        "order": GENERATION_ORDER,
        "memory": memory_items or [],
        "memoryActive": bool(memory_active),
        "signatureInMemory": bool(signature_in_memory),
        "alreadyDone": already_done or [],
        "uiLanguages": [{"code": c, "name": n} for c, n in UI_LANGUAGES],
        "uiLang": ui_lang or "en",
        "L": L,
    }
    data_json = json.dumps(data, ensure_ascii=False)

    html = r"""<div style="padding: 1rem 0;">
<h2 id="srTitle" class="sr-only"></h2>

<div style="margin-bottom: 16px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
  <label for="uiLang" style="font-size: 12px; color: var(--color-text-tertiary);"></label>
  <select id="uiLang" style="font-size: 12px; padding: 2px 6px; border-radius: 4px; border: 0.5px solid var(--color-border-tertiary); background: var(--color-background-primary);"></select>
</div>

<div id="memBox" style="margin-bottom: 16px; padding: 12px 14px; background: var(--color-background-secondary); border-radius: var(--border-radius-md); font-size: 13px;"></div>

<div style="margin-bottom: 16px;">
  <label id="offerLabel" for="offer" style="display:block; font-size: 13px; color: var(--color-text-secondary); margin-bottom: 6px;"></label>
  <textarea id="offer" rows="3" style="width:100%; box-sizing:border-box; font-family: inherit; font-size: 13px; padding: 8px 10px; border-radius: var(--border-radius-md); border: 0.5px solid var(--color-border-primary); resize: vertical;"></textarea>
</div>

<p id="docsHeading" style="font-size: 13px; color: var(--color-text-secondary); margin: 0 0 8px;"></p>
<label id="toggleAllDelivWrap" style="display:flex; align-items:center; gap:10px; padding:8px 12px; margin-bottom: 8px; border:0.5px dotted var(--color-border-tertiary); border-radius: var(--border-radius-md); background: var(--color-background-secondary); cursor:pointer; user-select:none;">
  <input type="checkbox" id="toggleAllDeliv" style="margin: 0;" />
  <span id="toggleAllDelivLabel" style="font-size: 12px; color: var(--color-text-secondary); font-style: italic;"></span>
</label>
<div id="deliverables" style="display: grid; gap: 8px; margin-bottom: 16px;"></div>

<div id="signatureZone" style="display:none; margin-bottom: 16px; padding: 12px 14px; background: var(--color-background-secondary); border-radius: var(--border-radius-md); font-size: 13px;"></div>

<div style="display:flex; align-items:center; gap:12px;">
  <button id="genBtn" style="font-size: 14px; padding: 8px 18px;"></button>
  <span id="hint" style="font-size: 12px; color: var(--color-text-tertiary);"></span>
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

  // ---- Static labels (from the interface-language label set) ----
  document.getElementById("srTitle").textContent = L.widget_aria;
  document.querySelector('label[for="uiLang"]').textContent = L.ui_language_label;
  document.getElementById("offerLabel").textContent = L.offer_label;
  document.getElementById("offer").placeholder = L.offer_placeholder;
  document.getElementById("docsHeading").textContent = L.documents_heading;
  document.getElementById("genBtn").textContent = L.generate_button;

  // ---- Interface-language selector (2B: changing it re-renders the widget) ----
  var uiSel = document.getElementById("uiLang");
  D.uiLanguages.forEach(function(l){
    var o = document.createElement("option");
    o.value = l.code; o.textContent = l.name;
    if (l.code === D.uiLang) o.selected = true;
    uiSel.appendChild(o);
  });
  var oOther = document.createElement("option");
  oOther.value = "other"; oOther.textContent = L.ui_language_other;
  uiSel.appendChild(oOther);
  uiSel.addEventListener("change", function(){
    var code = uiSel.value, msg;
    if (code === "other"){
      msg = "The user wants an interface language that is not in the list. Ask them which language (ISO code), then re-display the application-tools selection widget with its interface fully in that language (translate every visible label). Keep the deliverables language unchanged.";
    } else {
      var name = uiSel.options[uiSel.selectedIndex].text;
      msg = "Re-display the application-tools selection widget with its interface fully in " + name + " (" + code + "): translate every visible label into that language and pre-select it. Keep the deliverables language unchanged.";
    }
    if (typeof sendPrompt === "function"){ sendPrompt(msg); }
  });

  // ---- Memory block (editable) ----
  var memBox = document.getElementById("memBox");
  if (!D.memoryActive){
    memBox.innerHTML = '<span style="color: var(--color-text-tertiary);">'+esc(L.mem_paused)+'</span>';
  } else if (D.memory && D.memory.length){
    var header = '<div style="font-weight:500; margin-bottom:8px;">'+esc(L.mem_header)+' <span style="font-weight:400; font-size:11px; color: var(--color-text-tertiary);">'+esc(L.mem_header_note)+'</span></div>';
    var rowsHtml = D.memory.map(function(m, idx){
      var iid = "mem_" + (m.id || idx);
      // All fields are editable by default; a few may be marked editable:false (rare)
      var editable = m.editable !== false;
      if (editable){
        return '<div style="display:grid; grid-template-columns: 130px 1fr; gap:8px; align-items:center; margin:4px 0;">'
             + '<label for="'+iid+'" style="color: var(--color-text-secondary); font-size:12px;">'+esc(m.label)+'</label>'
             + '<input type="text" id="'+iid+'" class="mem-input" data-key="'+esc(m.id||m.label)+'" value="'+esc(m.value)+'" style="font-size:12px; padding: 4px 6px; border-radius: 4px; border: 0.5px solid var(--color-border-tertiary); background: var(--color-background-primary);" />'
             + '</div>';
      } else {
        return '<div style="margin:4px 0;"><span style="color: var(--color-text-secondary);">'+esc(m.label)+' :</span> '+esc(m.value)+'</div>';
      }
    }).join("");
    var saveOption = '<label style="display:flex; align-items:center; gap:6px; margin-top:10px; font-size:12px; color: var(--color-text-secondary); cursor:pointer;">'
                   + '<input type="checkbox" id="saveMem" /> '+esc(L.mem_save_option)
                   + '</label>';
    memBox.innerHTML = header + rowsHtml + saveOption;
  } else {
    memBox.innerHTML = '<span style="color: var(--color-text-tertiary);">'+esc(L.mem_none)+'</span>';
  }

  // ---- Deliverables ----
  var container = document.getElementById("deliverables");
  D.deliverables.forEach(function(d){
    var done = D.alreadyDone.indexOf(d.id) !== -1;
    var row = document.createElement("label");
    row.style.cssText = "display:flex; align-items:flex-start; gap:10px; padding:10px 12px; border:0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-md); cursor:pointer;"+(done?" opacity:0.55;":"");
    var cb = document.createElement("input");
    cb.type = "checkbox";
    cb.value = d.id;
    cb.className = "deliv";
    cb.dataset.id = d.id;
    cb.style.cssText = "margin-top:2px;";
    if (done){ cb.checked = true; cb.disabled = true; }
    var txt = document.createElement("div");
    var doneTag = done ? ' <span style="font-size:11px; color: var(--color-text-success);">'+esc(L.deliv_done_tag)+'</span>' : '';
    txt.innerHTML = '<div style="font-size:13px; font-weight:500;">'+esc(d.label)+doneTag+'</div>'+
                    '<div style="font-size:12px; color: var(--color-text-secondary);">'+esc(d.desc)+'</div>';
    row.appendChild(cb); row.appendChild(txt);
    container.appendChild(row);
    // Listener for the signature zone (appears if cover_letter is checked)
    if (d.id === "cover_letter"){
      cb.addEventListener("change", updateSignatureZone);
    }
  });

  // ---- Signature zone (conditional) ----
  function updateSignatureZone(){
    var sigZone = document.getElementById("signatureZone");
    var coverChecked = false;
    document.querySelectorAll(".deliv").forEach(function(cb){
      if (cb.dataset.id === "cover_letter" && cb.checked) coverChecked = true;
    });
    if (!coverChecked){
      sigZone.style.display = "none";
      sigZone.innerHTML = "";
      return;
    }
    sigZone.style.display = "block";
    var html = '<div style="font-weight:500; margin-bottom:8px;">'+esc(L.sig_title)+'</div>';

    if (D.memoryActive && D.signatureInMemory){
      // Case 1: memory active + signature available
      html += '<div style="color: var(--color-text-secondary); margin-bottom: 6px;">'+esc(L.sig_found)+'</div>';
      html += '<label style="display:flex; align-items:center; gap:6px; font-size:12px; cursor:pointer;">'
            + '<input type="checkbox" id="sigSkip" /> '+esc(L.sig_skip)
            + '</label>';
    } else if (D.memoryActive && !D.signatureInMemory){
      // Case 2: memory active but no signature
      html += '<div style="color: var(--color-text-secondary); margin-bottom: 6px;">'+esc(L.sig_none)+'</div>';
      html += '<label style="display:flex; align-items:center; gap:6px; font-size:12px; cursor:pointer; margin-bottom: 4px;">'
            + '<input type="checkbox" id="sigMemorize" /> '+esc(L.sig_memorize)
            + '</label>';
      html += '<div style="font-size:11px; color: var(--color-text-tertiary);">'+esc(L.sig_none_hint)+'</div>';
    } else {
      // Case 3: memory paused
      html += '<div style="color: var(--color-text-secondary); margin-bottom: 6px;">'+esc(L.sig_paused)+'</div>';
      html += '<div style="font-size:11px; color: var(--color-text-tertiary);">'+esc(L.sig_paused_hint)+'</div>';
    }
    sigZone.innerHTML = html;
  }

  // ---- "check all / uncheck all" logic ----
  // Generic helper: syncs the label and the master state with the children
  function setupToggleAll(masterSelector, labelSelector, childSelector){
    var master = document.querySelector(masterSelector);
    var label = document.querySelector(labelSelector);
    if (!master || !label) return;

    function getEnabledChildren(){
      return Array.prototype.slice.call(document.querySelectorAll(childSelector))
        .filter(function(c){ return !c.disabled; });
    }

    function updateMasterFromChildren(){
      var children = getEnabledChildren();
      if (children.length === 0){
        // No actionable child: hide the wrapper
        var wrap = master.parentElement;
        if (wrap) wrap.style.display = "none";
        return;
      }
      var allChecked = children.every(function(c){ return c.checked; });
      var noneChecked = children.every(function(c){ return !c.checked; });
      master.checked = allChecked;
      master.indeterminate = !allChecked && !noneChecked;
      label.textContent = allChecked ? L.toggle_all_uncheck : L.toggle_all_check;
    }

    master.addEventListener("change", function(){
      var children = getEnabledChildren();
      var newState = master.checked;
      children.forEach(function(c){
        if (c.checked !== newState){
          c.checked = newState;
          // Manually trigger the attached listeners (signature zone)
          c.dispatchEvent(new Event("change"));
        }
      });
      label.textContent = newState ? L.toggle_all_uncheck : L.toggle_all_check;
      master.indeterminate = false;
    });

    // Listen to each child to update the master
    getEnabledChildren().forEach(function(c){
      c.addEventListener("change", updateMasterFromChildren);
    });

    // Initial state
    updateMasterFromChildren();
  }

  setupToggleAll("#toggleAllDeliv", "#toggleAllDelivLabel", ".deliv");

  function enOf(id){
    var d = D.deliverables.filter(function(x){return x.id===id;})[0];
    return d ? d.en : id;
  }
  function moduleOf(id){
    var d = D.deliverables.filter(function(x){return x.id===id;})[0];
    return d ? d.module : "";
  }

  document.getElementById("genBtn").onclick = function(){
    var chosen = [];
    document.querySelectorAll(".deliv:checked:not(:disabled)").forEach(function(cb){ chosen.push(cb.value); });

    if (chosen.length === 0){
      document.getElementById("hint").textContent = L.hint_min_one;
      return;
    }

    // Collect the memory values (potentially modified)
    var memValues = {};
    var memModified = false;
    document.querySelectorAll(".mem-input").forEach(function(inp){
      var k = inp.dataset.key;
      var v = inp.value.trim();
      memValues[k] = v;
      // Compare with the original value
      var orig = (D.memory.filter(function(m){return (m.id||m.label)===k;})[0]||{}).value || "";
      if (v !== orig) memModified = true;
    });
    var saveMem = document.getElementById("saveMem");
    var saveMemChecked = saveMem ? saveMem.checked : false;

    // Signature: determine the instruction depending on the case
    var coverCovered = chosen.indexOf("cover_letter") !== -1;
    var sigSkip = document.getElementById("sigSkip");
    var sigMemorize = document.getElementById("sigMemorize");
    var sigInstruction = "";
    if (coverCovered){
      if (D.memoryActive && D.signatureInMemory){
        sigInstruction = (sigSkip && sigSkip.checked)
          ? "For this letter, do NOT use the available signature (generate without a signature)."
          : "Use the available signature (resolved by resolve_files.py from the project file or a session upload), passed to fill_cover_letter.py via --signature-base64.";
      } else if (D.memoryActive && !D.signatureInMemory){
        var memo = (sigMemorize && sigMemorize.checked)
          ? " If an image is attached, encode it via setup_signature.py and save it as a project file after use."
          : " If an image is attached, use it for this letter only (no saving).";
        sigInstruction = "Look for a signature image in the conversation attachments (PNG/JPG/GIF/BMP)." + memo + " If nothing is attached, generate without a signature.";
      } else {
        sigInstruction = "Memory paused: look for a signature image in the attachments (PNG/JPG/GIF/BMP). If found, use it for this letter only. Otherwise, generate without a signature.";
      }
    }

    // Order the standard deliverables per the imposed order
    var ordered = D.order.filter(function(id){ return chosen.indexOf(id) !== -1; });

    var offer = (document.getElementById("offer").value || "").trim();

    // The directive prompt below is ENGLISH-CANONICAL (Claude-facing), never localized.
    var lines = [];
    lines.push("Generate the following application tools:");
    ordered.forEach(function(id, i){
      lines.push((i+1) + ". " + enOf(id) + "  [module: " + moduleOf(id) + "]");
    });
    lines.push("");
    lines.push("Generate all the documents. Offer PDF export at the end.");
    lines.push("");
    lines.push("Production constraints:");
    lines.push("- File naming: <Type>_<Name>_<Company>_<Language> with hyphens inside compound names (e.g. Strategic_Playbook_Jordan-Lee-Carter_Acme-Financial-Group_EN). Do not abbreviate to Acme_Group.");
    lines.push("- The reference card recaps the essentials of the other documents: pitch, key points and Q&A. Fill it with every block (pitch, top_points, quick_qa, questions_to_ask, checklist).");
    lines.push("- If a script fails on the JSON format, read its structure reference and fix the JSON. NEVER work around it via the API or a homemade script.");

    // Candidate-data block (if the memory block is shown)
    if (Object.keys(memValues).length > 0){
      lines.push("");
      lines.push("Candidate data to use for this application:");
      Object.keys(memValues).forEach(function(k){
        lines.push("- " + k + " : " + memValues[k]);
      });
      if (memModified){
        if (saveMemChecked){
          lines.push("");
          lines.push("\u26a0\ufe0f I edited some data above: SAVE these changes to memory (via memory_user_edits).");
        } else {
          lines.push("");
          lines.push("\u2139\ufe0f I edited some data above: ONE-OFF use for this application only, do not modify memory.");
        }
      }
    }

    // Signature block (if cover_letter is checked)
    if (sigInstruction){
      lines.push("");
      lines.push("Signature (cover letter):");
      lines.push("- " + sigInstruction);
    }

    if (offer){
      lines.push("");
      lines.push("Job posting:");
      lines.push(offer);
    }

    var msg = lines.join("\n");
    if (typeof sendPrompt === "function"){ sendPrompt(msg); }
  };
})();
</script>"""

    html = html.replace("__DATA__", data_json)
    return html


def main():
    parser = argparse.ArgumentParser(
        description="Builds the application-tools selection widget (HTML)"
    )
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--memory-json", default="")
    parser.add_argument(
        "--memory-active", default="true", help="'true' or 'false': is memory active?"
    )
    parser.add_argument(
        "--signature-in-memory",
        default="false",
        help="'true' or 'false': is a signature available?",
    )
    parser.add_argument("--already-done-json", default="")
    parser.add_argument(
        "--ui-lang",
        default="en",
        help="Current interface-language code, to pre-select the dropdown (model sets it = memory preference if any, else conversation language).",
    )
    parser.add_argument(
        "--labels-json",
        default="",
        help="Optional. Visible labels in the interface language. If given, must carry the EXACT LABELS_EN key set.",
    )
    args = parser.parse_args()

    def parse_opt(s, default):
        if not s:
            return default
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            print(f"\u274c Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    memory_items = parse_opt(args.memory_json, [])
    already_done = parse_opt(args.already_done_json, [])
    memory_active = str(args.memory_active).lower() != "false"
    signature_in_memory = str(args.signature_in_memory).lower() == "true"

    # Resolve the visible labels: English-canonical base, overridden by
    # --labels-json (which must carry the exact key set — no half-localized UI).
    labels = dict(LABELS_EN)
    if args.labels_json:
        supplied = parse_opt(args.labels_json, {})
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
        memory_items,
        memory_active,
        signature_in_memory,
        already_done,
        args.ui_lang,
        labels,
    )
    out = Path(args.output_path)
    out.write_text(html, encoding="utf-8")
    print(f"\u2705 Selection widget generated: {out}")
    print(
        f"   - {len(memory_items)} memory item(s), memory {'active' if memory_active else 'paused'}, signature {'available' if signature_in_memory else 'absent'}"
    )
    print(
        f"   - interface language: {args.ui_lang}{' (localized labels supplied)' if args.labels_json else ' (English default labels)'}"
    )
    print(f"   - {len(already_done)} already done")


if __name__ == "__main__":
    main()
