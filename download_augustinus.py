import requests
from bs4 import BeautifulSoup
import os
import time
import re

def extract_title(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    return title.strip()

def process_urls():
    # For storing failed URLs
    failed_urls = []
    
    # Read URLs from links_failed.txt
    with open('links_failed.txt', 'r') as file:
        base_urls = [line.strip() for line in file if line.strip()]
    
    for base_url in base_urls:
        try:
            # Extract base part and numeric part from URL
            # Example: https://www.augustinus.it/latino/commento_lsg/omelia_00_testo.htm
            #          We'll get base_part = "https://www.augustinus.it/latino/commento_lsg/omelia_"
            #          and suffix = "_testo.htm"
            match = re.match(r'(.*?)(\d+)(.*?)$', base_url)
            if not match:
                print(f"Could not parse URL format: {base_url}")
                failed_urls.append(base_url)
                continue
                
            base_part = match.group(1)  # Everything before the number
            initial_num = int(match.group(2))  # The number part
            suffix = match.group(3)  # Everything after the number
            
            # Extract content name from URL for filename
            # Example: from "commento_lsg/omelia_00_testo.htm" we want "commento_lsg"
            path_parts = base_url.split('/')
            content_name = path_parts[-2] if len(path_parts) >= 2 else "content"
            
            # Output filename
            output_filename = f"{content_name}.txt"
            
            combined_content = ""
            current_num = initial_num
            found_pages = False
            
            print(f"Processing {base_url}...")
            
            # Process pages until a 404 is encountered
            while True:
                # Format the number based on the initial format (same number of digits)
                num_digits = len(match.group(2))
                formatted_num = f"{current_num:0{num_digits}d}"
                
                # Construct the URL with the incremented number
                url = f"{base_part}{formatted_num}{suffix}"
                
                print(f"Trying URL: {url}")
                
                try:
                    response = requests.get(url)
                    if response.status_code != 200:
                        print(f"Page not found: {url}")
                        break
                    
                    found_pages = True
                    html_content = response.text
                    title = extract_title(html_content)
                    
                    # Parse content
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract text content
                    body_content = soup.body.get_text(separator='\n', strip=True)
                    
                    # Check for frame content
                    if "La pagina corrente utilizza i frame" in body_content:
                        print(f"Detected frame content, trying to get actual content...")
                        # Look for frame source URL
                        frame_src = None
                        frames = soup.find_all('frame')
                        for frame in frames:
                            if 'src' in frame.attrs:
                                frame_src = frame['src']
                                # If relative URL, make it absolute
                                if not frame_src.startswith('http'):
                                    base_domain = re.match(r'(https?://[^/]+)', base_url).group(1)
                                    frame_src = f"{base_domain}{frame_src if frame_src.startswith('/') else '/' + frame_src}"
                                break
                        
                        if frame_src:
                            print(f"Found frame source: {frame_src}")
                            response = requests.get(frame_src)
                            if response.status_code == 200:
                                html_content = response.text
                                soup = BeautifulSoup(html_content, 'html.parser')
                                body_content = soup.body.get_text(separator='\n', strip=True)
                                title = extract_title(html_content)
                    
                    # Add title and content to the combined content
                    combined_content += f"\n\n{'=' * 50}\n{title}\n{'=' * 50}\n\n"
                    combined_content += body_content
                    
                    print(f"Successfully processed: {url}")
                    
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                    break
                
                # Increment number for next iteration
                current_num += 1
                
                # Add a small delay to avoid overloading the server
                time.sleep(1)
            
            # Save combined content if any pages were found
            if found_pages:
                with open(output_filename, 'w', encoding='utf-8') as file:
                    file.write(combined_content)
                print(f"Saved content to {output_filename}")
            else:
                print(f"No valid pages found for {base_url}")
                failed_urls.append(base_url)
        
        except Exception as e:
            print(f"Failed to process {base_url}: {e}")
            failed_urls.append(base_url)
    
    # Save failed URLs to links_failed_new.txt
    if failed_urls:
        with open('links_failed_new.txt', 'w') as file:
            for url in failed_urls:
                file.write(f"{url}\n")
        print(f"Saved {len(failed_urls)} failed URLs to links_failed_new.txt")
    else:
        print("All URLs were processed successfully!")

if __name__ == "__main__":
    process_urls() 