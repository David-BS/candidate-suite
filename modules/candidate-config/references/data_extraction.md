# Extracting data from a CV

## Fundamental principle

**If the user provides a CV in the conversation, ALWAYS use it as the primary data source.**

Do NOT manually ask the user for information that is already in the CV. It's a waste of time and a bad user experience.

## Extraction workflow

### Step 1: Identify the source

The CV can be in several places:
- `/mnt/user-data/uploads/` (uploaded in the current conversation)
- `/mnt/project/` (in the project files, Project Files mode)

### Step 2: Read the content

Read the CV **directly** with the `view` tool (or the file-reading skill for less common formats):
```python
view(path="/mnt/user-data/uploads/CV_Jordan_Lee-Carter.docx")
```
The model reads the CV and extracts the fields itself, in **any language** — there is no regex extractor (removed in LNG-2 S3; reading meaning is *fond*, a model task).

### Step 3: Extract the fields

Fields to look for in the CV (read them from the document, in whatever language it is written):

| Field | Where to look |
|-------|---------------|
| First + Last name | Usually at the top of the CV, in large type. |
| Email | The email address in the contact block. |
| Phone | The phone number in the contact block (any national/international format). |
| Address | Street, postal code and city in the contact block (any country's format). |
| LinkedIn | The `linkedin.com/in/…` URL — copy it **verbatim**. |
| GitHub (optional) | The `github.com/…` URL, if present. |
| Portfolio (optional) | Any personal/portfolio URL mentioned. |

### Step 4: Present to the user

Recommended format:

```
I extracted from your CV:

📋 Detected data:
  Name        : Jordan Lee-Carter
  Email       : jordan.lee@example.com
  Phone       : +33 6 12 34 56 78
  LinkedIn    : linkedin.com/in/jordan-lee-carter

[If some fields are missing from the CV:]
To complete, I need your postal address.
```

### Step 5: Validation and saving

1. Wait for the user's validation (or corrections)
2. Save the validated data with `memory_user_edits add`
3. Format: see `references/memory_format.md`

## Error cases

### No CV available
Ask the user to provide the data manually.

### Incomplete extraction
Clearly indicate which fields could not be extracted:

```
I was able to extract from your CV:
  Name        : Jordan Lee-Carter ✓
  Email       : jordan.lee@example.com ✓
  
Fields not found in the CV:
  Address     : ?
  Phone       : ?

Can you provide them directly?
```

### Uncertain data
If a field is ambiguous (e.g. several addresses in the CV), ask for confirmation:

```
I found 2 addresses in your CV:
  1. 12 Example Street, 75001 Paris
  2. 45 Test Avenue, 69002 Lyon

Which is your current address?
```

## Anti-patterns to avoid

❌ **Manually asking for what's in the CV**
```
[CV provided with email visible]
Claude: "What's your email?"  ← NO
```

❌ **Asking for confirmation field by field**
```
Claude: "Is it Jordan?"
User: "Yes"
Claude: "Is it Lee-Carter?"
User: "Yes"  ← Present everything at once instead
```

❌ **Ignoring the provided CV**
```
Claude: "OK I'll ask you for the info..."
[Without having read the CV]  ← NO, read first
```

## Best practices

✅ **Read the CV before asking questions**  
✅ **Present all extracted fields at once** for grouped validation  
✅ **Clearly indicate the source** ("I extracted from your CV...")  
✅ **Ask only for what's missing** (typically the address if not present)  
✅ **Respect the provided format** (e.g. if a phone is in `06.12.34.56.78`, don't reformat it to `+33 6 12 34 56 78` without asking)
