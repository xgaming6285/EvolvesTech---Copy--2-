#!/usr/bin/env python3
import os
import re
from collections import defaultdict

# Base directory to scan
BASE_DIR = "evolves/www.evolves.tech"

# File extensions and their cache settings
CACHE_SETTINGS = {
    # Static assets that rarely change - long cache
    'long': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.otf'],
        'cache_control': 'public, max-age=31536000, immutable'  # 1 year
    },
    # Code assets that might change with each deployment - use cache busting
    'code': {
        'extensions': ['.css', '.js', '.json'],
        'cache_control': 'public, max-age=31536000, immutable'  # 1 year (assuming cache busting)
    },
    # HTML and XML - short cache with revalidation
    'content': {
        'extensions': ['.html', '.htm', '.xml'],
        'cache_control': 'public, max-age=3600, must-revalidate'  # 1 hour
    }
}

# Default headers for all paths
DEFAULT_HEADERS = """/*
  Cache-Control: max-age=3600, must-revalidate
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
"""

# Default "no cache" rule for anything not matched
DEFAULT_NO_CACHE = """# Default for anything not matched: no cache, to be safe
/*
  Cache-Control: no-cache, no-store, must-revalidate
  Pragma: no-cache
  Expires: 0
"""

def generate_headers_file():
    """Scan directory and generate _headers file with appropriate caching rules."""
    # Dictionary to store all found paths by cache type
    found_paths = defaultdict(set)
    
    # Check if base directory exists
    if not os.path.exists(BASE_DIR):
        print(f"Error: Directory '{BASE_DIR}' not found!")
        return
    
    # Walk through all directories and files
    for root, dirs, files in os.walk(BASE_DIR):
        rel_path = os.path.relpath(root, BASE_DIR)
        if rel_path == ".":
            rel_path = ""
        
        # Ensure forward slashes in paths (for Netlify)
        rel_path = rel_path.replace("\\", "/")
        
        # Process each file
        for file in files:
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Determine cache category
            cache_category = None
            for category, settings in CACHE_SETTINGS.items():
                if ext in settings['extensions']:
                    cache_category = category
                    break
            
            if cache_category:
                # Create the relative path pattern
                if rel_path:
                    path_pattern = f"/{rel_path}/*.{ext[1:]}"
                else:
                    path_pattern = f"/*.{ext[1:]}"
                
                found_paths[cache_category].add(path_pattern)
    
    # Generate the _headers file content
    headers_content = [DEFAULT_HEADERS]
    
    # Add rules for each category
    for category, settings in CACHE_SETTINGS.items():
        paths = sorted(found_paths[category])
        if paths:
            headers_content.append(f"# Cache {category} files")
            for path in paths:
                headers_content.append(f"{path}")
                headers_content.append(f"  Cache-Control: {settings['cache_control']}")
            headers_content.append("")
    
    # Add Netlify's immutable assets rules
    headers_content.append("# Netlify's immutable assets (often hashed)")
    headers_content.append("/_netlify/static/*")
    headers_content.append("  Cache-Control: public, max-age=31536000, immutable")
    headers_content.append("/_netlify/images/*")
    headers_content.append("  Cache-Control: public, max-age=31536000, immutable")
    headers_content.append("")
    
    # Add default "no cache" rule
    headers_content.append(DEFAULT_NO_CACHE)
    
    # Write to _headers file in the publish directory
    headers_file_path = os.path.join(BASE_DIR, "_headers")
    with open(headers_file_path, "w") as f:
        f.write("\n".join(headers_content))
    
    print(f"Generated _headers file in {headers_file_path} with {sum(len(paths) for paths in found_paths.values())} cache rules.")

if __name__ == "__main__":
    generate_headers_file() 