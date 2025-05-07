import os
import argparse
import minify_html
from bs4 import BeautifulSoup
import cssmin
import jsmin

def find_html_files(folder_path):
    """
    Finds all HTML files in the given folder and its subdirectories.
    """
    html_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".html") or file.endswith(".htm"):
                html_files.append(os.path.join(root, file))
    return html_files

def optimize_html_file(file_path):
    """
    Optimizes the given HTML file by minifying its content, adding lazy loading to images,
    minifying inline CSS and JS, and deferring external scripts.
    """
    print(f"Optimizing {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Image Optimization: Add loading="lazy" to all img tags
        for img_tag in soup.find_all("img"):
            img_tag["loading"] = "lazy"
            print(f"  Added loading='lazy' to image: {img_tag.get('src', 'N/A')}")

        # 2. CSS Optimization: Minify content of <style> tags
        for style_tag in soup.find_all("style"):
            if style_tag.string:
                minified_css = cssmin.cssmin(style_tag.string)
                style_tag.string = minified_css
                print("  Minified inline CSS in <style> tag.")

        # 3. JavaScript Optimization:
        # Minify inline JS in <script> tags (not having a 'src' attribute)
        for script_tag in soup.find_all("script"):
            if script_tag.string and not script_tag.has_attr("src"):
                try:
                    minified_js = jsmin.jsmin(script_tag.string)
                    script_tag.string = minified_js
                    print("  Minified inline JavaScript in <script> tag.")
                except Exception as e:
                    print(f"  Could not minify inline script: {e}")
            # Add defer to external scripts if not already async or defer
            elif script_tag.has_attr("src") and not (script_tag.has_attr("async") or script_tag.has_attr("defer")):
                script_tag["defer"] = True
                print(f"  Added defer to script: {script_tag['src']}")

        # Get the modified HTML from BeautifulSoup
        optimized_html_content = str(soup)

        # Minify the whole HTML structure using minify-html
        final_minified_html = minify_html.minify(optimized_html_content.encode('utf-8'), 
                                                minify_css=True, 
                                                minify_js=True).decode('utf-8')

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_minified_html)
        print(f"Successfully optimized and minified {file_path}")
    except Exception as e:
        print(f"Error optimizing {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Find and optimize WordPress HTML files in a folder.")
    parser.add_argument("folder", help="The path to the folder to scan.")
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: Folder not found at {args.folder}")
        return

    html_files = find_html_files(args.folder)

    if not html_files:
        print(f"No HTML files found in {args.folder}")
        return

    print(f"Found {len(html_files)} HTML file(s):")
    for f_path in html_files:
        print(f" - {f_path}")
        optimize_html_file(f_path)

    print("\nOptimization process complete.")

if __name__ == "__main__":
    main()
