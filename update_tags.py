import os
from bs4 import BeautifulSoup, NavigableString
import re

# Regex to find internal image URLs in CSS: url(path/to/image.ext)
# Captures:
# Group 1: Optional quote (' or ")
# Group 2: The internal image path (e.g., "wp-content/uploads/image.jpg")
CSS_URL_PATTERN = re.compile(
    r'url\s*\(\s*(["\']?)(?!https?://|//|data:)([^\s)"\']*\.(?:png|jpg|jpeg))\1\s*\)',
    re.IGNORECASE
)
# If paths with spaces *inside unquoted* url() are common and need to be supported,
# the path part `[^\s)"\']*` might need to be `.+?` but that requires careful testing.
# For standard CSS, `url(path with space.png)` is invalid; it should be `url("path with space.png")`.
# The current regex: url\s*\(\s*(["\']?)(?!https?://|//|data:)(.+?\.(?:png|jpg|jpeg))\1\s*\)
# This one is generally more robust for various path characters if properly quoted or simple.
CSS_URL_PATTERN = re.compile(
    r'url\s*\(\s*(["\']?)(?!https?://|//|data:)(.+?\.(?:png|jpg|jpeg))\1\s*\)',
    re.IGNORECASE
)


def replace_css_image_path_to_webp(match_obj):
    """Callback function for re.sub to replace image extension in a CSS url() path."""
    quote = match_obj.group(1)
    image_path = match_obj.group(2)
    new_image_path = re.sub(r'\.(png|jpg|jpeg)$', '.webp', image_path, flags=re.IGNORECASE)
    return f'url({quote}{new_image_path}{quote})'

def update_css_text_content(css_text):
    """
    Updates internal image URLs to .webp within a string of CSS content.
    Returns the modified CSS text and a boolean indicating if changes were made.
    """
    modified_css_text, num_replacements = CSS_URL_PATTERN.subn(replace_css_image_path_to_webp, css_text)
    return modified_css_text, num_replacements > 0

def process_srcset_attribute(srcset_value):
    """
    Processes a srcset attribute string, converting internal image URLs to .webp.
    Returns the modified srcset string and a boolean indicating if changes were made.
    """
    if not srcset_value:
        return srcset_value, False

    parts = srcset_value.split(',')
    new_parts = []
    changed_overall = False
    for i, part_str in enumerate(parts):
        stripped_part = part_str.strip()
        if not stripped_part:
            # Preserve spacing for empty parts if they are not the last one,
            # or if the original part_str was just spaces.
            if stripped_part != part_str or (i < len(parts) -1 and not part_str):
                 new_parts.append(part_str)
            continue

        url_match = re.match(r'([^\s]+)(\s+.*)?', stripped_part)
        if not url_match:
            new_parts.append(part_str) # Should ideally not happen if stripped_part is non-empty
            continue

        url = url_match.group(1)
        descriptor = url_match.group(2) if url_match.group(2) else ""
        
        is_internal_image = (
            not url.startswith(('https://', '//', 'data:')) and
            re.search(r'\.(png|jpg|jpeg)$', url, re.IGNORECASE)
        )

        if is_internal_image:
            new_url = re.sub(r'\.(png|jpg|jpeg)$', '.webp', url, flags=re.IGNORECASE)
            if new_url != url:
                changed_overall = True
            new_parts.append(new_url + descriptor)
        else:
            new_parts.append(stripped_part)

    if changed_overall:
        return ', '.join(new_parts), True
    return srcset_value, False


def process_html_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        soup = BeautifulSoup(content, 'html.parser')
        file_modified_overall = False

        # --- Process <img> tags ---
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            original_src = img_tag.get('src')
            original_srcset = img_tag.get('srcset') # Save for evolves.tech logic
            tag_modified_this_iteration = False

            # 1. Initial Skip (mimicking original script's first skip condition for <img>)
            if original_src and original_src.startswith('https://') and not original_srcset:
                continue

            # 2. Process 'src' attribute: convert to .webp if internal
            current_src = img_tag.get('src')
            if current_src and not current_src.startswith(('https://', '//', 'data:')):
                if re.search(r'\.(png|jpg|jpeg)$', current_src, re.IGNORECASE):
                    new_src = re.sub(r'\.(png|jpg|jpeg)$', '.webp', current_src, flags=re.IGNORECASE)
                    if new_src != current_src:
                        img_tag['src'] = new_src
                        tag_modified_this_iteration = True
            
            # 3. Process 'srcset' attribute: convert internal images to .webp
            current_srcset = img_tag.get('srcset')
            if current_srcset:
                modified_srcset_val, srcset_content_changed = process_srcset_attribute(current_srcset)
                if srcset_content_changed:
                    img_tag['srcset'] = modified_srcset_val
                    tag_modified_this_iteration = True
            
            # 4. evolves.tech cleanup specific to <img>
            final_src_on_tag = img_tag.get('src') # Get src after potential .webp conversion
            final_src_is_internal = (final_src_on_tag and 
                                     not final_src_on_tag.startswith(('https://', '//', 'data:')))
            
            original_srcset_had_evolves = (original_srcset and 
                                           'https://www.evolves.tech/wp-content' in original_srcset)

            if final_src_is_internal and original_srcset_had_evolves:
                if img_tag.has_attr('srcset'): # Check if srcset still exists (it might have been modified)
                    del img_tag['srcset']
                    tag_modified_this_iteration = True # Ensure modification is flagged
            
            if tag_modified_this_iteration:
                file_modified_overall = True

        # --- Process <link> tags (for href attributes pointing to images) ---
        link_tags = soup.find_all('link')
        for link_tag in link_tags:
            original_href = link_tag.get('href')
            # Skip if no href, or href is external/data URI
            if not original_href or original_href.startswith(('https://', '//', 'data:')):
                continue

            # Check if it's a PNG, JPG, or JPEG file (case-insensitive)
            if re.search(r'\.(png|jpg|jpeg)$', original_href, re.IGNORECASE):
                new_href = re.sub(r'\.(png|jpg|jpeg)$', '.webp', original_href, flags=re.IGNORECASE)
                if new_href != original_href: # Ensure change actually happens
                    link_tag['href'] = new_href
                    file_modified_overall = True
        
        # --- Process <source> tags (for srcset attributes) ---
        source_tags = soup.find_all('source')
        for source_tag in source_tags:
            original_srcset = source_tag.get('srcset')
            if original_srcset: # process_srcset_attribute handles internal/external logic
                modified_srcset, srcset_changed = process_srcset_attribute(original_srcset)
                if srcset_changed:
                    source_tag['srcset'] = modified_srcset
                    file_modified_overall = True

        # --- Process <style> tags ---
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            css_changed_in_this_tag = False
            new_style_contents = [] # To build the new content for the style tag
            
            for item in style_tag.contents:
                if isinstance(item, NavigableString):
                    original_css_chunk = str(item)
                    modified_css_chunk, chunk_was_changed = update_css_text_content(original_css_chunk)
                    if chunk_was_changed:
                        css_changed_in_this_tag = True
                    new_style_contents.append(NavigableString(modified_css_chunk))
                else: # Keep comments or other non-string nodes as they are
                    new_style_contents.append(item.copy()) # Append a copy to avoid issues if modifying tree elsewhere
            
            if css_changed_in_this_tag:
                style_tag.clear() # Remove old contents
                for new_node in new_style_contents:
                    style_tag.append(new_node) # Add new/modified contents
                file_modified_overall = True
        
        # --- Process style attributes on all tags ---
        # Find all tags that *have* a style attribute
        tags_with_style_attr = soup.find_all(attrs={"style": True})
        for tag_with_style in tags_with_style_attr:
            original_style_value = tag_with_style.get('style')
            if original_style_value: # Ensure it's not empty or None
                modified_style_value, style_attr_changed = update_css_text_content(original_style_value)
                if style_attr_changed:
                    tag_with_style['style'] = modified_style_value
                    file_modified_overall = True
        
        if file_modified_overall:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(str(soup)) # Use str(soup) for minimal structural changes
            print(f"Modified: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.html'):
                file_path = os.path.join(root, file_name)
                process_html_file(file_path)

if __name__ == "__main__":
    directory = input("Enter the directory path containing HTML files: ")
    if os.path.isdir(directory):
        process_directory(directory)
        print("Processing complete.")
    else:
        print("Invalid directory path.")