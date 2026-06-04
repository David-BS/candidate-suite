# Claude memory format

This module uses `memory_user_edits` to store the configuration persistently.

## Standard structure

Each entry starts with a prefix identifying its type:
- `[CONFIG] ...`: technical configuration (storage mode, filenames, style)
- `[CANDIDAT] ...`: the candidate's personal data

## Full example

```
[CONFIG] Storage method: project_files
[CONFIG] CV filename: CV_Jordan_Lee-Carter.docx
[CONFIG] Signature filename: signature_jordan_b64.txt
[CONFIG] Template filename: Cover_letter_template.docx
[CONFIG] Header style: hybrid
[CANDIDAT] First name: Jordan
[CANDIDAT] Last name: Lee-Carter
[CANDIDAT] Full name: Jordan Lee-Carter
[CANDIDAT] Street: 12 Example Street
[CANDIDAT] Postal code: 75001
[CANDIDAT] City: Paris
[CANDIDAT] Email: jordan.lee@example.com
[CANDIDAT] Phone: +33 6 12 34 56 78
[CANDIDAT] LinkedIn: https://linkedin.com/in/jordan-lee-carter
```

## Supported fields

### [CONFIG] — technical configuration

| Field | Possible values | Required |
|-------|-----------------|----------|
| `Storage method` | `project_files` \| `stateless` | ✅ |
| `Header style` | `hybrid` \| `block` | ✅ (default `hybrid`) |
| `CV filename` | CV filename | Mode-dependent |
| `Signature filename` | Signature filename (usually base64 .txt) | Mode-dependent |
| `Template filename` | Neutral cover-letter template name | Mode-dependent |

### [CANDIDAT] — personal data

| Field | Description | Required |
|-------|-------------|----------|
| `First name` | First name | ✅ |
| `Last name` | Last name | ✅ |
| `Full name` | Full name (may differ from "First + Last" if compound) | ✅ |
| `Street` | Postal address | ✅ |
| `Postal code` | Postal code | ✅ |
| `City` | City | ✅ |
| `Email` | Primary email address | ✅ |
| `Phone` | Phone number | ✅ |
| `LinkedIn` | LinkedIn profile URL | ✅ |
| `Portfolio` | Portfolio URL (optional) | ❌ |
| `GitHub` | GitHub URL (optional) | ❌ |

## Common operations

### Read the current config

```python
memory_user_edits(command="view")
```

Mentally filter the lines starting with `[CONFIG]` and `[CANDIDAT]`.

### Add a field

```python
memory_user_edits(command="add", control="[CANDIDAT] Email: new@example.com")
```

### Update an existing field

1. `view` to list the entries
2. Identify the line number of the field to change
3. Use `replace`:

```python
memory_user_edits(command="replace", line_number=8, replacement="[CANDIDAT] Email: new@example.com")
```

### Delete a field

```python
memory_user_edits(command="remove", line_number=8)
```

## Edge cases

### Special characters

Apostrophes, accents and UTF-8 characters are supported:
- ✅ `[CANDIDAT] Street: 12 rue de la Paix`
- ✅ `[CANDIDAT] City: Saint-Étienne`
- ✅ `[CANDIDAT] City: L'Haÿ-les-Roses`

### Long URLs

For long URLs, keep the compact format:
- ✅ `[CANDIDAT] LinkedIn: https://linkedin.com/in/jordan-lee-carter`
- ❌ `[CANDIDAT] LinkedIn URL of Jordan Lee-Carter: https://www.linkedin.com/in/jordanlee-12345/`

### Phone: supported formats
- `+33 6 12 34 56 78` (French format with spaces)
- `+33 6.12.34.56.78` (French format with `.` separators)
- `06 12 34 56 78` (national format)
- `+1 (555) 123-4567` (US format)

Preserve the format provided by the user.

### Cleanup on reset

On `"Reset my config"`:
1. `view` to list all entries
2. Filter those with the `[CONFIG]` or `[CANDIDAT]` prefix
3. Delete them one by one with `remove`
4. Confirm with the user

## Technical limits

- Max 30 entries in memory (all types combined)
- Max 100000 characters per entry
- No sensitive information (SSN, passwords, account numbers, etc.)

## Best practices

- **Always `view` before `remove` or `replace`**: line numbers can change between sessions
- **Prefix consistency**: always use exactly `[CONFIG]` or `[CANDIDAT]` (with brackets, space after)
- **One datum per entry**: don't put several fields on one line
- **Prefixes unique to this module**: to make filtering and reset easier
