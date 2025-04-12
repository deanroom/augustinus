#!/usr/bin/env python3
import os
import time
import requests
from bs4 import BeautifulSoup
import re

# Base URL and directory setup
BASE_URL = "https://www.augustinus.it/latino/lettere/lettera_{:03d}_testo.htm"
OUTPUT_DIR = "augustinus_letters"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_letter(letter_num):
    """Download a specific letter by number"""
    url = BASE_URL.format(letter_num)
    
    try:
        print(f"Downloading letter {letter_num} from {url}")
        response = requests.get(url)
        
        # If page doesn't exist, return False
        if response.status_code != 200:
            print(f"Letter {letter_num} not found. Status code: {response.status_code}")
            return False
            
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main content - usually within certain HTML elements
        # This may need adjustment based on the actual structure of the website
        main_content = soup.find('div', class_='corpoargomento') or soup
        
        # Extract title
        title_tag = main_content.find(['h3', 'h2', 'h1']) or main_content.find(string=re.compile(r'EPISTOLA \d+'))
        title = title_tag.get_text().strip() if title_tag else f"EPISTOLA {letter_num}"
        
        # Extract letter information
        content_parts = []
        
        # Add the title
        content_parts.append(title)
        content_parts.append("\n" + "="*len(title) + "\n")
        
        # Extract metadata if available (date, recipient, etc.)
        metadata = main_content.find('i')
        if metadata:
            content_parts.append(metadata.get_text().strip() + "\n")
        
        # Add section titles and paragraphs
        for element in main_content.find_all(['p', 'h4', 'h5']):
            text = element.get_text().strip()
            if text:
                if element.name in ['h4', 'h5']:
                    content_parts.append("\n" + text + "\n" + "-"*len(text) + "\n")
                else:
                    content_parts.append(text + "\n")
        
        # Join all content parts
        full_content = "\n".join(content_parts)
        
        # Save the content to a file
        filename = os.path.join(OUTPUT_DIR, f"lettera_{letter_num:03d}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        print(f"Successfully saved letter {letter_num} to {filename}")
        return True
        
    except Exception as e:
        print(f"Error downloading letter {letter_num}: {e}")
        return False

def main():
    # Starting letter number
    letter_num = 1
    
    # Maximum number of consecutive failed attempts before stopping
    max_failures = 5
    consecutive_failures = 0
    
    print(f"Starting download of Augustine's letters from {BASE_URL.format(letter_num)}")
    print(f"Letters will be saved to the '{OUTPUT_DIR}' directory")
    
    while consecutive_failures < max_failures:
        success = download_letter(letter_num)
        
        if success:
            consecutive_failures = 0  # Reset failure counter on success
        else:
            consecutive_failures += 1
            print(f"Failed to download letter {letter_num}. Attempts left: {max_failures - consecutive_failures}")
            
        letter_num += 1
        
        # Be nice to the server with a delay between requests
        time.sleep(2)
        
    print(f"Download completed. Found letters 1 to {letter_num - consecutive_failures - 1}")
    print(f"All letters have been saved to the '{OUTPUT_DIR}' directory")

if __name__ == "__main__":
    main() 