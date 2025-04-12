import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urlparse

def extract_title(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    return title.strip()

def process_urls(limit=None):
    # Read URLs from the file
    with open('links2.txt', 'r') as file:
        base_urls = [line.strip() for line in file if line.strip()]
    
    # Limit to the first URL if requested
    if limit:
        base_urls = base_urls[:limit]
    
    for base_url in base_urls:
        # Extract the base path and content name
        parsed_url = urlparse(base_url)
        path_parts = parsed_url.path.split('/')
        content_name = path_parts[-2] if len(path_parts) >= 2 else ""
        
        # Base URL without 'index.htm'
        base_path = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(path_parts[:-1])}/"
        
        # Create output filename based on content name
        output_filename = f"{content_name}.txt"
        
        combined_content = ""
        page_number = 1
        found_pages = False
        
        print(f"Processing {base_url}...")
        
        # Process pages until a 404 is encountered
        while True:
            # 所有页面都使用 _libro.htm 后缀
            url = f"{base_path}{content_name}_{page_number}_libro.htm"
            
            print(f"Trying URL: {url}")
            
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    print(f"Page not found: {url}")
                    # 尝试替代URL格式
                    if page_number > 1:
                        alt_url = f"{base_path}{content_name}_{page_number}.htm"
                        print(f"Trying alternative URL: {alt_url}")
                        response = requests.get(alt_url)
                        if response.status_code != 200:
                            break
                        url = alt_url
                    else:
                        break
                
                found_pages = True
                html_content = response.text
                title = extract_title(html_content)
                
                # Parse content
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract text content (modify as needed based on actual page structure)
                body_content = soup.body.get_text(separator='\n', strip=True)
                
                # 检查是否包含框架错误信息
                if "La pagina corrente utilizza i frame" in body_content:
                    print(f"Detected frame content, trying to get actual content...")
                    # 查找框架源URL
                    frame_src = None
                    frames = soup.find_all('frame')
                    for frame in frames:
                        if 'src' in frame.attrs:
                            frame_src = frame['src']
                            if not frame_src.startswith('http'):
                                frame_src = f"{parsed_url.scheme}://{parsed_url.netloc}{frame_src if frame_src.startswith('/') else '/' + frame_src}"
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
            
            # Increment page number for next iteration
            page_number += 1
            
            # Add a small delay to avoid overloading the server
            time.sleep(1)
        
        # Save combined content if any pages were found
        if found_pages:
            with open(output_filename, 'w', encoding='utf-8') as file:
                file.write(combined_content)
            print(f"Saved content to {output_filename}")
        else:
            print(f"No valid pages found for {base_url}")

if __name__ == "__main__":
    # Process all URLs
    process_urls() 