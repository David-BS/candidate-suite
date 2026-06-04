# Quick Reference Card structure

A **one-page** card to print/check right before each interview.
Principle: everything must be punchy and scannable in a few seconds.

## Sections

### pitch_short
The story / pitch in condensed form, to memorize. 3-5 sentences max.
JSON format: string.

### key_stats
4-6 key figures to know by heart (years of exp, quantified achievements,
striking metrics). Format: list of short strings.

### top_points
The 3 points to land for sure during the interview, each with its proof.
Format: `[{"point": "...", "evidence": "..."}, ...]`

### quick_qa
3-5 frequent questions + express answers (1-2 sentences each).
Format: `[{"q": "...", "a": "..."}, ...]`

### questions_to_ask
4-6 strategic questions to ask the recruiter. Format: list of strings.

### checklist
Final checklist before the interview (mental preparation, logistics, etc.).
Format: list of strings (each item rendered with a checkbox).

## Full JSON expected

```json
{
  "candidate_name": "...",
  "job_title": "...",
  "company_name": "...",
  "date": "...",
  "pitch_short": "text...",
  "key_stats": ["10 years of experience", "€2B processed/year", "..."],
  "top_points": [
    {"point": "...", "evidence": "..."}
  ],
  "quick_qa": [
    {"q": "...", "a": "..."}
  ],
  "questions_to_ask": ["...", "..."],
  "checklist": ["...", "..."]
}
```

All content sections are optional: include only what is relevant and fits on
one page.

## Condensing principle

- The figures and positioning must be CONSISTENT with the source documents
  (summary, interview prep, playbook). Don't reinvent.
- Prefer ultra-short phrasing: it's a memory aid, not a lecture.
- If the sources are long, select the essentials (the 3 points that really
  matter, the 5 most striking stats).
