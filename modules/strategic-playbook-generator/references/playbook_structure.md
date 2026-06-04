# Strategic Playbook structure

The playbook is a strategic working document. It is longer than the other
deliverables (2-5 pages) because it serves as a "bible" before the interviews.

## Sections (the JSON mirrors this structure)

Each section is optional in the JSON: include only those that add value for
this particular application. At minimum: context, pain points, positioning,
per-round strategy, questions to ask.

### 1. company_context
Who the company / entity is, what characterizes it, how the role fits in. If web
search was done: recent news and strategy.
JSON format: string (text, may contain markdown bullets `-`).

### 2. pain_points
List of the major issues the company is trying to solve through this role.
For each: the problem + the candidate's response angle.
Format: `[{"title": "...", "analysis": "...", "your_angle": "..."}, ...]`

### 3. org_landscape
Organizational dynamics: who decides, stakeholders, tensions typical of the
context. Stay factual or clearly analytical (no invented gossip).
Format: string.

### 4. positioning
The candidate's key messages (2-4), each with proof drawn from the CV.
Format: `[{"message": "...", "evidence": "..."}, ...]`

### 5. interview_strategy
Strategy tailored to each known round (screening, technical, final, etc.).
Format: `[{"round": "...", "focus": "...", "approach": "..."}, ...]`

### 6. questions_to_ask
Smart questions to ask the recruiter (showing the candidate is also evaluating).
Format: list of strings.

### 7. tough_questions
Anticipated tough questions + response strategy.
Format: `[{"question": "...", "strategy": "..."}, ...]`

### 8. thirty_second_pitch
Short, punchy version of the positioning (string).

### 9. red_lines
Points to clarify / watch-outs before accepting the role.
Format: list of strings.

## Full JSON expected by generate_playbook.py

```json
{
  "candidate_name": "...",
  "job_title": "...",
  "company_name": "...",
  "date": "...",
  "web_research_done": true,
  "company_context": "text...",
  "pain_points": [
    {"title": "...", "analysis": "...", "your_angle": "..."}
  ],
  "org_landscape": "text...",
  "positioning": [
    {"message": "...", "evidence": "..."}
  ],
  "interview_strategy": [
    {"round": "...", "focus": "...", "approach": "..."}
  ],
  "questions_to_ask": ["...", "..."],
  "tough_questions": [
    {"question": "...", "strategy": "..."}
  ],
  "thirty_second_pitch": "text...",
  "red_lines": ["...", "..."]
}
```

The `web_research_done` field (boolean) lets the document indicate whether the
context relies on web search or only on the posting + CV.

## Tips in the playbook

Use tips sparingly (the playbook is already dense):
- A callout tip `> [!TIP-BOX]` at the top can recap how to use the doc.
- Occasional side-note tips `> [!TIP]` on high-stakes sections.

These markers are handled automatically by the script (see generate_playbook.py).

## Truthfulness principle

- Facts about the company: only if reliable (web or user-provided).
- Sector analysis: allowed but presented as analysis, not as fact.
- Candidate proof: drawn from the real CV, never invented.
