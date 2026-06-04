# Cover-letter header styles

This module supports 2 header styles for the sender's address block (top-left of the cover letter).

## Overview

| Mode | Lines | Character |
|------|-------|-----------|
| **Hybrid** (default) | 3 | Compact, modern, digital contact details grouped |
| **Block** | 6 | Classic, each piece of info on its own line |

## Hybrid mode (default)

### Visual layout
```
│ Jordan Lee-Carter
│ 12 Example Street, 75001 Paris
│ jordan.lee@example.com | linkedin.com/in/jordan-lee-carter | +33 6 12 34 56 78
```

### Structure
- **Line 1**: Full name (bold, blue #1F497D, Calibri 14pt)
- **Line 2**: Full address on one line (street, postal code, city separated by commas) - Calibri 10pt
- **Line 3**: Digital contact details (email, LinkedIn, phone) separated by ` | ` - Calibri 10pt
  - Email and LinkedIn: blue #0000FF, underlined (hyperlinks)
  - Phone: normal color

### Use cases
- Modern profiles (tech, startups, agencies)
- When a compact header is wanted to save space
- A clean, professional look

## Block mode

### Visual layout
```
│ Jordan Lee-Carter
│ 12 Example Street
│ 75001 Paris
│ jordan.lee@example.com
│ linkedin.com/in/jordan-lee-carter
│ +33 6 12 34 56 78
```

### Structure
- **Line 1**: Full name (bold, blue #1F497D, Calibri 14pt)
- **Line 2**: Street only (Calibri 10pt)
- **Line 3**: Postal code + city (Calibri 10pt)
- **Line 4**: Email (blue #0000FF, underlined, Calibri 10pt)
- **Line 5**: LinkedIn (blue #0000FF, underlined, Calibri 10pt)
- **Line 6**: Phone (Calibri 10pt)

### Use cases
- Classic corporate profiles (banking, consulting, legal)
- When the user prefers a traditional layout
- Compatibility with stricter ATS (Applicant Tracking Systems)

## Common technical characteristics

The 2 modes share these characteristics:

### Font
- **Calibri** (Sans Serif) for the whole block
- Name: 14pt bold
- Rest: 10pt normal

### Colors
- Name: dark blue #1F497D
- Email and LinkedIn: blue #0000FF, underlined (hyperlinks)
- Rest: black

### Border
- **Left border only**:
  - Style: Single
  - Color: Light gray #C0C0C0
  - Width: 1pt
  - Border/text spacing: ~2mm

### Presentation to the user (in chat)
To show the examples:
- Use `│` (Unicode character U+2502 BOX DRAWINGS LIGHT VERTICAL) to simulate the left border
- **NO full frame** (no top/bottom/right borders)
- Use the user's **real data** in the examples (no placeholders)

## User-question workflow

### Case 1: First configuration (no style in memory)

Present the 2 options with concrete examples:

```
How would you like to lay out your address block at the top of the letters?

HYBRID mode (default) — 3 compact lines:

│ [User's name]
│ [Street], [Postal code] [City]
│ [Email] | [LinkedIn] | [Phone]

BLOCK mode — 6 classic lines:

│ [User's name]
│ [Street]
│ [Postal code] [City]
│ [Email]
│ [LinkedIn]
│ [Phone]

Keep HYBRID as the default, or prefer BLOCK?
```

### Case 2: Changing the style (existing style in memory)

```
Your current header style is: HYBRID

│ [Example with user data in HYBRID]

Do you want to change it to BLOCK?

│ [Example with user data in BLOCK]
```

## Storage in memory

The style is stored in Claude's memory:
```
[CONFIG] Header style: hybrid
```
or
```
[CONFIG] Header style: block
```

## Impact on template generation

The `scripts/generate_templates.py` script accepts a `--style` parameter:

```bash
# Generate in Hybrid mode (default)
python scripts/generate_templates.py --style hybrid /mnt/user-data/outputs/

# Generate in Block mode
python scripts/generate_templates.py --style block /mnt/user-data/outputs/
```

If the style is changed after the templates are created, **regenerating the templates** is recommended for consistency.

## Recommendation

- **By default**: Hybrid mode
- **On explicit request**: Block mode
- **When in doubt**: Hybrid mode (more modern, compatible with most contexts)
