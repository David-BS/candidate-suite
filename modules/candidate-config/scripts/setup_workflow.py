"""
Script that prints the critical outputs of the initial setup workflow.

Ensures the outputs (questions, checks, recap) are always formatted EXACTLY as
expected, with no risk of improvisation.

Usage:
    python setup_workflow.py <action> [args...]

Actions:
    storage_question                              : Storage-mode question
    name_check --extracted-name "X Y Z"           : Name-consistency check (3+ words)
    final_recap --json '{"full_name":"X",...}'    : Final recap
"""

import argparse
import json


def storage_question():
    """Prints the persistence-mode question (no connector)."""
    print("""Persistence mode:

A. Project file (recommended) — drop CV/signature/tracker once into the project files
B. No persistence — re-upload each session

Which mode do you choose?""")


def name_check(extracted_name):
    """Checks whether a name contains a space in the middle and offers the options."""
    parts = extracted_name.strip().split()
    if len(parts) < 3:
        # No ambiguity (1 or 2 words)
        return False

    # 3+ words → potential hyphen ambiguity
    # E.g.: "Jordan Lee Carter" could be "Jordan Lee-Carter"
    last_parts = parts[1:]
    last_with_space = " ".join(last_parts)
    last_with_hyphen = "-".join(last_parts)

    print(f"""The CV shows "{extracted_name}". Is your last name:

A. {last_with_space} (two separate words)
B. {last_with_hyphen} (hyphenated)

Which option?""")
    return True


def final_recap(data_json):
    """Prints the final configuration recap."""
    data = json.loads(data_json)

    full_name = data.get("full_name", "?")
    street = data.get("street", "?")
    postal = data.get("postal_code", "?")
    city = data.get("city", "?")
    email = data.get("email", "?")
    phone = data.get("phone", "?")
    linkedin = data.get("linkedin", "?")
    storage = data.get("storage_method", "?")
    cv_filename = data.get("cv_filename", "?")
    signature_filename = data.get("signature_filename", "?")
    template_filename = data.get("template_filename", "Cover_letter_template.docx")
    templates_source = data.get("templates_source", "generated (Hybrid)")

    print(f"""✅ Configuration saved

📋 Profile:
  Name       : {full_name}
  Address    : {street}, {postal} {city}
  Email      : {email}
  Phone      : {phone}
  LinkedIn   : {linkedin}

🛠️ Configuration:
  Storage       : {storage}
  CV            : {cv_filename}
  Signature     : {signature_filename}
  Template      : {template_filename}
  Templates source : {templates_source}

You can now generate cover letters. If you want to change
anything, tell me for example "change my email" or
"update my CV".""")


def main():
    parser = argparse.ArgumentParser(description="Setup workflow outputs")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # storage_question
    subparsers.add_parser("storage_question")

    # name_check
    p_name = subparsers.add_parser("name_check")
    p_name.add_argument("--extracted-name", required=True)

    # final_recap
    p_recap = subparsers.add_parser("final_recap")
    p_recap.add_argument("--json", required=True)

    args = parser.parse_args()

    if args.action == "storage_question":
        storage_question()
    elif args.action == "name_check":
        name_check(args.extracted_name)
    elif args.action == "final_recap":
        final_recap(args.json)


if __name__ == "__main__":
    main()
