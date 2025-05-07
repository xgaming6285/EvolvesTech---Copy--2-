import argparse
import sys
import os
import glob # For finding files
from bs4 import BeautifulSoup
from cssmin import cssmin
from jsmin import jsmin, JavascriptMinify

def minify_css_content(css_code):
    """Minifies CSS content."""
    try:
        return cssmin(css_code)
    except Exception as e:
        print(f"Warning: Could not minify CSS in a block. Error: {e}", file=sys.stderr)
        return css_code

def minify_js_content(js_code):
    """Minifies JavaScript content."""
    try:
        return jsmin(js_code)
    except JavascriptMinify as e:
        print(f"Warning: Could not minify JavaScript in a block. Error: {e}", file=sys.stderr)
        return js_code
    except Exception as e:
        print(f"Warning: Could not minify JavaScript in a block due to an unexpected error: {e}", file=sys.stderr)
        return js_code

def process_html_file(filepath):
    """
    Reads an HTML file, minifies inline CSS and JavaScript,
    and overwrites the original file.
    """
    print(f"Processing '{filepath}' for in-place minification...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        return # Continue to next file if one is not found in batch mode
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    changes_made = False

    # Minify inline CSS in <style> tags
    style_tags_minified = 0
    for style_tag in soup.find_all('style'):
        if style_tag.string: # Check if the tag has content
            original_css = style_tag.string
            minified_css = minify_css_content(original_css)
            if minified_css != original_css:
                style_tag.string.replace_with(minified_css)
                style_tags_minified +=1
                changes_made = True

    # Minify inline JavaScript in <script> tags (excluding those with a 'src' attribute)
    script_tags_minified = 0
    for script_tag in soup.find_all('script'):
        if not script_tag.has_attr('src') and script_tag.string: # Check if inline and has content
            original_js = script_tag.string
            minified_js = minify_js_content(original_js)
            if minified_js != original_js:
                script_tag.string.replace_with(minified_js)
                script_tags_minified += 1
                changes_made = True
    
    if not changes_made:
        print(f"No inline <style> or <script> content was minified in '{filepath}'. File unchanged.")
        return

    modified_html_content = soup.prettify()

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_html_content)
        print(f"Successfully minified and overwrote '{filepath}' (Styles minified: {style_tags_minified}, Scripts minified: {script_tags_minified})")
    except Exception as e:
        print(f"Error writing (overwriting) file '{filepath}': {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description=(
            'Minify inline CSS and JavaScript within HTML file(s) by overwriting them. \n'
            'WARNING: This script directly modifies the input files. Make sure to backup your files before running.'
        ),
        formatter_class=argparse.RawTextHelpFormatter # To keep the warning format
    )
    parser.add_argument(
        'input_path',
        help='Path to the input HTML file or a directory containing HTML files to be overwritten.'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively search for HTML files in subdirectories of input_path if it is a directory.'
    )

    args = parser.parse_args()
    input_path = args.input_path

    if os.path.isfile(input_path):
        if not (input_path.lower().endswith(".html") or input_path.lower().endswith(".htm")):
            print(f"Error: Input file '{input_path}' is not an HTML file (.html or .htm).", file=sys.stderr)
            sys.exit(1)
        process_html_file(input_path)
    elif os.path.isdir(input_path):
        print(f"Processing directory: '{input_path}' for in-place minification.")
        print("WARNING: Files in this directory (and subdirectories if --recursive) will be overwritten.")
        
        # Simplified glob pattern construction
        if args.recursive:
            patterns = [os.path.join(input_path, '**', '*.html'), os.path.join(input_path, '**', '*.htm')]
        else:
            patterns = [os.path.join(input_path, '*.html'), os.path.join(input_path, '*.htm')]

        all_files_to_process = []
        for pattern in patterns:
            all_files_to_process.extend(glob.glob(pattern, recursive=args.recursive))
        
        # Remove duplicates that might occur if a file is .html and picked by **/*.html and **/*.htm
        all_files_to_process = sorted(list(set(all_files_to_process)))

        if not all_files_to_process:
            print(f"No HTML files (.html or .htm) found in '{input_path}' {'recursively' if args.recursive else 'at the top level'}.")
            sys.exit(0)

        for filepath_to_process in all_files_to_process:
            process_html_file(filepath_to_process)
        print(f"Processed {len(all_files_to_process)} HTML file(s).")
    else:
        print(f"Error: Input path '{input_path}' is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main() 