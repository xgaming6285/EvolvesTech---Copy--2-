import os
import re
import argparse

# The HTML snippet to insert
TAGS_TO_INSERT = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>"""

# Specific parts to check for existence to avoid duplication
# We check for the hrefs as they are quite unique to these tags
CHECK_STRINGS = [
    'href="https://fonts.googleapis.com"',
    'href="https://fonts.gstatic.com"'
]

def modify_html_file(file_path):
    """
    Modifies a single HTML file to add the preconnect links after the <head> tag.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return
    except UnicodeDecodeError as e:
        print(f"Error decoding file {file_path} as UTF-8: {e}. Skipping.")
        return


    # 1. Check if the tags (or significant parts of them) already exist
    already_exists = all(check_str in content for check_str in CHECK_STRINGS)
    if already_exists:
        print(f"Skipped (tags likely already exist): {file_path}")
        return

    # 2. Find the opening <head> tag (case-insensitive, handles attributes)
    # Regex: (<head\b[^>]*>)
    # - <head\b : Matches "<head" followed by a word boundary (to not match <header>)
    # - [^>]*  : Matches any character except '>' zero or more times (for attributes)
    # - >      : Matches the closing '>'
    # - (...)  : Capturing group for the entire matched <head ...> tag
    head_regex = re.compile(r'(<head\b[^>]*>)', re.IGNORECASE)
    match = head_regex.search(content)

    if not match:
        print(f"Skipped (no <head> tag found): {file_path}")
        return

    # The full opening <head ...> tag
    original_head_tag = match.group(1)
    
    # Construct the new content to insert right after the original <head> tag
    # We add a newline after the original tag, then our tags, then another newline
    # for better readability in the source HTML.
    insertion_string = f"\n{TAGS_TO_INSERT}\n"
    
    # Replace the first occurrence of the original_head_tag with itself + new tags
    # Using a lambda function with re.sub ensures we only modify the first match
    # and correctly insert after the captured group.
    modified_content, num_replacements = head_regex.subn(
        lambda m: m.group(1) + insertion_string,
        content,
        count=1 # Replace only the first occurrence
    )

    if num_replacements > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"Modified: {file_path}")
        except IOError as e:
            print(f"Error writing to file {file_path}: {e}")
    else:
        # This case should technically be caught by "if not match" earlier,
        # but it's a good safeguard.
        print(f"Skipped (head tag found but no replacement made, unexpected): {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Adds Google Fonts preconnect links to HTML files in a folder."
    )
    parser.add_argument(
        "folder_path",
        type=str,
        help="The path to the folder containing HTML files."
    )
    args = parser.parse_args()

    folder_path = args.folder_path

    if not os.path.isdir(folder_path):
        print(f"Error: The path '{folder_path}' is not a valid directory.")
        return

    print(f"Scanning folder: {folder_path}\n")

    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith((".html", ".htm")):
                file_path = os.path.join(root, filename)
                print(f"Processing: {file_path}")
                modify_html_file(file_path)
                print("-" * 20)

    print("\nScript finished.")

if __name__ == "__main__":
    main()