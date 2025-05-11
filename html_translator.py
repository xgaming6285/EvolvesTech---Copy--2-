from bs4 import BeautifulSoup, NavigableString
import os
import re # Import the regular expression module

def clean_internal_spacing(text):
    """Replaces multiple whitespace characters with a single space."""
    if text:
        # Replace multiple spaces/tabs/newlines with a single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip() # Also strip leading/trailing again after cleaning
    return text

def extract_texts_for_translation(html_filepath, output_text_filepath):
    """
    Extracts visible text from an HTML file, cleans internal spacing,
    and saves it for translation.
    Returns a list of (NavigableString_object, original_full_text_of_node, cleaned_stripped_text_of_node)
    and a list of unique cleaned stripped texts that were written to the file.
    """
    try:
        with open(html_filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: HTML file not found at {html_filepath}")
        return None, None

    soup = BeautifulSoup(html_content, 'html.parser')
    
    ignore_tags = ['script', 'style', 'head', 'title', 'meta', '[document]']
    
    text_nodes_info = [] # To store (NavigableString_object, original_full_text_of_node, cleaned_stripped_text_of_node)
    all_cleaned_stripped_texts_in_order = [] # Stores cleaned text for each node, in order of appearance

    for string_node in soup.find_all(string=True):
        if string_node.parent.name in ignore_tags:
            continue
        
        original_full_text_of_node = str(string_node)
        stripped_text = original_full_text_of_node.strip() # Initial strip

        if not stripped_text: # Skip if it's only whitespace after initial strip
            continue

        # Clean internal multiple spaces
        cleaned_stripped_text_of_node = clean_internal_spacing(stripped_text)

        if not cleaned_stripped_text_of_node: # Skip if it becomes empty after internal cleaning
            continue
        
        text_nodes_info.append((string_node, original_full_text_of_node, cleaned_stripped_text_of_node))
        all_cleaned_stripped_texts_in_order.append(cleaned_stripped_text_of_node)

    # Create a list of unique texts to write to the file, preserving order of first appearance
    unique_cleaned_texts_for_file = []
    seen_texts = set()
    for text in all_cleaned_stripped_texts_in_order:
        if text not in seen_texts:
            unique_cleaned_texts_for_file.append(text)
            seen_texts.add(text)
    
    with open(output_text_filepath, 'w', encoding='utf-8') as f:
        for text in unique_cleaned_texts_for_file:
            f.write(text + '\n')
            
    print(f"Extracted {len(unique_cleaned_texts_for_file)} unique text segments to {output_text_filepath}")
    # text_nodes_info contains all nodes.
    # unique_cleaned_texts_for_file is what's in the translation file.
    return text_nodes_info, unique_cleaned_texts_for_file


def apply_translations_to_html(original_html_filepath, translated_text_filepath, 
                               output_html_filepath, text_nodes_info, 
                               original_unique_cleaned_stripped_texts):
    """
    Applies translated texts back into the HTML structure.
    original_unique_cleaned_stripped_texts are the unique texts that were written to the translation file.
    text_nodes_info contains (node_object, original_full_text_of_node, cleaned_stripped_text_of_node) for ALL occurrences.
    """
    try:
        with open(translated_text_filepath, 'r', encoding='utf-8') as f:
            translated_lines = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: Translated text file not found at {translated_text_filepath}")
        return

    if len(translated_lines) != len(original_unique_cleaned_stripped_texts):
        print(f"Error: Mismatch in number of text segments. Original unique texts: {len(original_unique_cleaned_stripped_texts)}, Translated lines: {len(translated_lines)}")
        print("Please ensure each line in the translated file corresponds to a unique line in the original text file.")
        return

    # Create a mapping from the original cleaned & stripped unique text to its translation
    translation_map = {}
    for i, original_text in enumerate(original_unique_cleaned_stripped_texts):
        translation_map[original_text] = translated_lines[i]

    # --- IMPORTANT: Re-parse the HTML to get a fresh soup object for modification ---
    # This avoids issues with modifying a soup object that might have been altered
    # or whose node references are stale.
    try:
        with open(original_html_filepath, 'r', encoding='utf-8') as f:
            fresh_html_content = f.read()
        current_soup = BeautifulSoup(fresh_html_content, 'html.parser')
    except FileNotFoundError:
        print(f"Error: Original HTML file not found at {original_html_filepath} during re-parse.")
        return
    # --- End of re-parse ---

    replaced_count = 0
    
    # We need to find the nodes in the *current_soup* that correspond to text_nodes_info.
    # This is the most complex part. The original text_nodes_info contains direct references
    # to nodes in the *first* soup object. These references are not valid for current_soup.
    # We will iterate through current_soup and try to match based on original content.

    current_text_nodes_in_fresh_soup = []
    for string_node in current_soup.find_all(string=True):
        if string_node.parent.name in ['script', 'style', 'head', 'title', 'meta', '[document]']:
            continue
        original_full_text = str(string_node)
        stripped_text = original_full_text.strip()
        if not stripped_text:
            continue
        cleaned_stripped_text = clean_internal_spacing(stripped_text)
        if not cleaned_stripped_text:
            continue
        current_text_nodes_in_fresh_soup.append(
            (string_node, original_full_text, cleaned_stripped_text)
        )
    
    # Now, iterate through these found nodes and replace them
    # This assumes the order of text nodes found in fresh_soup is the same as initially extracted.
    # This is generally true for static HTML unless the parser behaves very differently.

    if len(current_text_nodes_in_fresh_soup) != len(text_nodes_info):
        print(f"Warning: Number of text nodes re-identified ({len(current_text_nodes_in_fresh_soup)}) "
              f"differs from initially extracted ({len(text_nodes_info)}). "
              "This might lead to incorrect replacements. Proceeding with caution.")
        # Heuristic: if significantly different, maybe abort or use a more complex matching.
        # For now, we'll try to proceed, but it's a potential issue.

    for node_to_replace_fresh, original_full_text_of_node, cleaned_stripped_text_of_node in current_text_nodes_in_fresh_soup:
        if cleaned_stripped_text_of_node in translation_map:
            translated_text_core = translation_map[cleaned_stripped_text_of_node]
            
            # Attempt to preserve original leading/trailing whitespace from the *full original text of this node*
            try:
                start_index = -1
                for i_char, char_val in enumerate(original_full_text_of_node):
                    if not char_val.isspace():
                        start_index = i_char
                        break
                
                end_index = -1
                for i_char, char_val in enumerate(reversed(original_full_text_of_node)):
                    if not char_val.isspace():
                        end_index = len(original_full_text_of_node) - 1 - i_char
                        break

                if start_index != -1 and end_index != -1 and start_index <= end_index :
                    leading_ws = original_full_text_of_node[:start_index]
                    trailing_ws = original_full_text_of_node[end_index+1:]
                    new_full_text_for_node = leading_ws + translated_text_core + trailing_ws
                elif start_index == -1: # Original was all whitespace (should have been skipped earlier)
                    new_full_text_for_node = translated_text_core # Should not happen if pre-filtered
                else: # Fallback for unusual cases
                    new_full_text_for_node = translated_text_core

            except Exception as e_ws:
                print(f"Warning: Could not robustly re-apply whitespace for '{cleaned_stripped_text_of_node[:30]}...'. Using translated text directly. Error: {e_ws}")
                new_full_text_for_node = translated_text_core

            try:
                if node_to_replace_fresh.parent: 
                    node_to_replace_fresh.replace_with(NavigableString(new_full_text_for_node))
                    replaced_count += 1
                else:
                    print(f"Warning: Node for '{cleaned_stripped_text_of_node[:30]}...' (original: '{original_full_text_of_node[:30]}...') is detached in fresh soup. Skipping.")
            except Exception as e_replace:
                print(f"Error replacing node for '{cleaned_stripped_text_of_node[:30]}...': {e_replace}")
        else:
            # This means a text node was found in the HTML that wasn't in the original unique list.
            # This could happen if the HTML structure is very dynamic or if our cleaning/uniqueness logic had an edge case.
            # Or, more likely, if the text content itself is not what we expected for matching.
            # For robustness, it's usually okay to leave these untranslated if no map entry exists.
            pass # print(f"Debug: No translation map entry for cleaned text: '{cleaned_stripped_text_of_node[:50]}...'")


    expected_replacements = sum(1 for _, _, cleaned_text_orig in text_nodes_info if cleaned_text_orig in translation_map)
    if replaced_count == 0 and expected_replacements > 0:
         print("Critical Warning: No text nodes were replaced, but translations were expected. "
               "This indicates a fundamental issue with re-identifying nodes for replacement.")
    elif replaced_count < expected_replacements:
        print(f"Warning: Not all expected text nodes were replaced. Expected (approx based on initial scan) {expected_replacements}, actually replaced {replaced_count}.")

    with open(output_html_filepath, 'w', encoding='utf-8') as f:
        f.write(str(current_soup)) # Use the modified current_soup
    print(f"Created translated HTML file: {output_html_filepath}")


# --- Configuration ---
INPUT_HTML_FILE = 'index.html'
TEXT_FOR_TRANSLATION_FILE = 'texts_to_translate.txt'
TRANSLATED_TEXT_FILE = 'translated_texts.txt' # You'll create this file
OUTPUT_HTML_FILE = 'translated_index.html'

def main():
    # --- Part 1: Extract texts ---
    print(f"Step 1: Extracting texts from {INPUT_HTML_FILE}...")
    # `nodes_info_initial_scan` contains (node_ref, original_full, cleaned_stripped) from the first parse
    # `unique_original_texts` is the list of unique cleaned texts written to the translation file
    nodes_info_initial_scan, unique_original_texts = extract_texts_for_translation(INPUT_HTML_FILE, TEXT_FOR_TRANSLATION_FILE)
    
    if nodes_info_initial_scan is None:
        return

    print(f"\nTexts extracted to '{TEXT_FOR_TRANSLATION_FILE}'.")
    print("Please translate this file using Google Translate (or any other method).")
    print(f"Ensure each line in the translated file corresponds to a line in '{TEXT_FOR_TRANSLATION_FILE}'.")
    print(f"Save the translated content as '{TRANSLATED_TEXT_FILE}' in the same directory.")
    
    input(f"\nPress Enter once you have created '{TRANSLATED_TEXT_FILE}'...")

    # --- Part 2: Apply translations ---
    if not os.path.exists(TRANSLATED_TEXT_FILE):
        print(f"Error: '{TRANSLATED_TEXT_FILE}' not found. Please create it and run the script again or press Enter after creating it.")
        return

    print(f"\nStep 2: Applying translations from '{TRANSLATED_TEXT_FILE}' to create '{OUTPUT_HTML_FILE}'...")
    apply_translations_to_html(
        INPUT_HTML_FILE, 
        TRANSLATED_TEXT_FILE, 
        OUTPUT_HTML_FILE,
        nodes_info_initial_scan, # Pass the node info from the initial scan
        unique_original_texts # Pass the unique texts that were translated
    )
    print("\nProcess complete.")

if __name__ == '__main__':
    main()