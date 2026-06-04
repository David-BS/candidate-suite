# Cover-letter conventions — letter-specific (agnostic)

> **Role.** The *letter-specific* layer of the agnostic style architecture (LNG-1, §7).
> It **presupposes** `language_style_generic.md` and adds **only** the epistolary layer of a
> formal job-application letter. It deliberately does **not** restate register, idiom, date,
> number, spacing, or label rules — those live in the generic resource, the single source of
> truth. (Discipline, validated 03/06: generic = base; letter = non-redundant complement.
> Two sources of truth on register would drift.)
>
> This resource **supersedes** the former `language_conventions.md` (which mixed generic and
> letter-specific FR/EN data). The generic half moved to `language_style_generic.md`; this is
> the letter half, made agnostic.

## What this resource does and does not touch

- **Does not touch layout.** The letter's visual skeleton — the `.docx` template: Calibri,
  single A4 page, margins, fused header-block borders, floating signature beside the
  signatory name, name-only under the signature, etc. — is a **non-negotiable formatting
  asset**. The model never reconstructs the `.docx` as prose; it only produces the **text**
  inserted into the template's named placeholders.
- **Does not touch structure.** The **5-paragraph structure** (§1 hook · §2 current role ·
  §3 prior relevant experience · §4 value proposition · §5 conclusion) is fixed — see
  `paragraph_structure.md`. This resource governs only the **language realization** of the
  letter's epistolary slots and the §4 phrasing stance.

## 1. Salutation (`GREETING` slot)

- **Recipient known by name** → address them with the conventional honorific + name form of
  the target culture for formal correspondence; include an academic/professional title if it
  applies and is conventional in that culture. Match the honorific form to what is known; if
  the appropriate form is uncertain, use a neutral conventional form rather than guess.
- **Recipient unknown** → use the standard impersonal **formal** salutation the target
  language uses to address an unnamed hiring recipient.

## 2. Subject line (`SUBJECT` slot)

- A concise application subject per the target culture's convention: a label meaning
  "position" / "application" followed by the **exact role title from the posting**.
- Apply the generic resource's locale punctuation-spacing to this line.

## 3. Complimentary close (`CLOSING` slot)

- A standard, formal-but-current professional sign-off conventional in the target culture.
  Prefer the **common professional default** over the most ceremonial/archaic option, unless
  the sector (e.g. a traditional institution) clearly calls for higher formality.
- Exactly **one** close, placed immediately above the signatory name.

## 4. Value-proposition paragraph (§4) — phrasing stance

- Realize §4 with **forward-looking, employer-oriented contribution phrasing** in the target
  language: framed as *what the candidate will bring to the organization / how the team will
  benefit*, as a future contribution backed by past quantified proof — **not** a past-tense
  self-summary (that would duplicate §2–§3).
- This is a phrasing **stance**, applied natively in the target language. Do not import
  ready-made phrasings from another language; produce the native equivalent.

## 5. Body register & addressing

- Per the generic resource: formal professional register (the formal/polite address form
  where the language marks one), native idiom. The letter is consistently addressed to the
  recipient / organization throughout.

## Named slots the model fills (in the target language)

`GREETING`, `SUBJECT`, the five body paragraphs (`§1`–`§5`), `CLOSING`.

Everything else is handled elsewhere: page layout and the signatory-name placement by the
template; date rendering, number/percent formatting, and punctuation spacing by the generic
resource.

> **Implementation note (placeholders).** These slots map to the **neutral** template
> placeholders `{{SUBJECT_LABEL}}`, `{{GREETING}}`, `{{CLOSING}}` of the single
> `Cover_letter_template.docx` (**L6 landed**). The model fills them in the run language;
> `subject_label` includes the label's separator and trailing space (e.g. `Poste : `).

## Discipline reminder

This resource names **only** epistolary specifics. Any rule about register, format, or idiom
*in general* belongs to `language_style_generic.md`, not here — one source of truth per rule,
to prevent drift.
