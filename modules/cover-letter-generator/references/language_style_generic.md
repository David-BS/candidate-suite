# Language & locale style — generic (applies to all candidate-suite deliverables)

> **Role.** This resource is the *generic* layer of the agnostic style architecture (LNG-1, §7).
> It replaces the former hand-maintained per-language data (the FR/EN anglicism table, the
> vouvoiement rule, the FR/EN date/number/spacing tables, label consistency) with
> **language-agnostic principles**. The model produces the deliverable's linguistic
> realization in the **confirmed target language** (the run's resolved `--language` value);
> this resource constrains *how*, **without enumerating any specific language's values**.
>
> Scope: **all five generators** (cover letter, application summary, interview prep,
> strategic playbook, quick reference). The letter adds an epistolary layer on top
> (`letter_conventions.md`), which *presupposes* this resource and never restates it.

## Pivot principle

Do not rely on a frozen FR/EN table for anything below. Resolve every point from the
**target language itself**, applying these principles. The list of structural sections of
each deliverable is **fixed** by that deliverable's structure spec (anti-hallucination
counterweight); only the **wording** is produced. Never add, drop, rename, or reorder sections.

## 1. Target language & register

- Write the **entire** deliverable in the confirmed target language. Do not mix languages,
  except for established proper nouns and established domain terms (see §2).
- Use the **formal professional register** standard for that language in a hiring context.
  Where the language grammaticalizes politeness or social distance (e.g. a T–V distinction,
  honorific levels, formal verb conjugations), default to the **formal/polite** form
  throughout. Never switch register mid-document.

## 2. Native idiom — avoid calques and loanwords

- Phrase **natively**. Avoid loan-translations (calques) and words borrowed from another
  language when the target language has an established native equivalent.
- **Exception:** established domain/industry terms that are the professional norm in the
  target language for that field — keep those; forcing a "native" replacement would read as
  unnatural. The test: write what a native professional **in that field** would actually write.

## 3. Dates

- Render dates in the conventional written form of the **target locale**: correct element
  ordering (day/month/year vs month/day/year as the locale dictates), the month named in the
  target language, and the locale-correct presence/absence of separators and leading particles.
- Avoid all-numeric or cross-locale-ambiguous date forms (a date that would read as a
  different day under another locale).

## 4. Numbers, percentages, units

- Use the **target locale's** thousands separator and decimal separator. These differ across
  locales (the roles of "." and "," can be swapped), so never carry one locale's convention
  into another.
- Apply the locale's spacing convention between a number and its unit or percent sign.

## 5. Punctuation spacing

- Apply the **target locale's** spacing rules around punctuation. Some locales require a
  space before certain marks (e.g. high punctuation such as `:` `;` `?` `!`, and inside their
  quotation marks); others require no space before punctuation. Follow the target locale; do
  not import another locale's spacing.
- Where the locale requires a space that must not break across a line, use a **non-breaking
  space** (`U+00A0`).

## 6. Label & terminology consistency

- Keep structural labels and recurring terminology **consistent within a single deliverable**
  (the same term for the same concept throughout).
- The set of structural labels/sections is **fixed** by the deliverable's structure spec.
  Produce the label text in the target language, but **never** add, drop, rename, or reorder
  sections. (This is the anti-hallucination counterweight to removing the frozen `TEXTS`
  tables: the structure is guaranteed; only its wording is generated.)

## 7. Quality bar (anti-drift)

- These principles **replace** the former per-language tables and must be applied with enough
  precision to match the quality those tables guaranteed: correct register, correct locale
  formats, natural idiom — leaving **no slack** that would invite a low-quality or
  hallucinated realization.
- If a specific convention of the target language is genuinely uncertain on some point,
  prefer the **most widely accepted formal convention** for that language and keep it
  internally consistent. Do not invent idiosyncratic forms.
