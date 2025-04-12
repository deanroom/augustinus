import requests
from bs4 import BeautifulSoup
import os
import time
import shutil
from urllib.parse import urlparse

def extract_title(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    return title.strip()

def process_urls(input_file='links2.txt', limit=None):
    # 用于存储失败的URL
    failed_urls = []
    
    # Read URLs from the file
    with open(input_file, 'r') as file:
        base_urls = [line.strip() for line in file if line.strip()]
    
    # Limit to the first URL if requested
    if limit:
        base_urls = base_urls[:limit]
    
    for base_url in base_urls:
        try:
            # Extract the base path and content name
            parsed_url = urlparse(base_url)
            path_parts = parsed_url.path.split('/')
            content_name = path_parts[-2] if len(path_parts) >= 2 else ""
            
            # Base URL without 'index.htm'
            base_path = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(path_parts[:-1])}/"
            
            # Create output filename based on content name
            output_filename = f"{content_name}.txt"
            
            combined_content = ""
            found_pages = False
            
            print(f"Processing {base_url}...")
            
            # 各种可能的URL模式
            url_patterns = [
                # 先尝试罗马数字模式 (i, ii, iii, iv, ...)
                lambda n: f"{base_path}{content_name}_{get_roman_numeral(n)}.htm",
                lambda n: f"{base_path}{content_name}_{get_roman_numeral(n)}_testo.htm",
                
                # 再尝试两位数格式
                lambda n: f"{base_path}{content_name}_{n:02d}_testo.htm",
                lambda n: f"{base_path}{content_name}_{n:02d}.htm",
                
                # 最后尝试普通数字格式
                lambda n: f"{base_path}{content_name}_{n}_testo.htm",
                lambda n: f"{base_path}{content_name}_{n}.htm",
                
            ]
            
            # 对网站的书籍格式进行尝试
            page_number = 1
            while page_number <= 30:  # 设置最大页数限制
                found_page = False
                
                for pattern_func in url_patterns:
                    url = pattern_func(page_number)
                    print(f"Trying URL: {url}")
                    
                    try:
                        response = requests.get(url)
                        if response.status_code == 200:
                            found_page = True
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
                            break  # 找到成功的URL后退出模式循环
                        
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
                
                if not found_page:
                    print(f"No valid URL found for page {page_number}")
                    break  # 如果当前页面的所有模式都失败，则退出
                
                # 成功找到页面后，增加页码继续查找下一页
                page_number += 1
                
                # 添加短暂延迟以避免过度请求服务器
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
    
    # 保存失败的URL到failure_file
    if failed_urls:
        failure_file = 'links_failed.txt'
        with open(failure_file, 'w') as file:
            for url in failed_urls:
                file.write(f"{url}\n")
        print(f"Saved {len(failed_urls)} failed URLs to {failure_file}")
    else:
        print("All URLs were processed successfully!")

def get_roman_numeral(n):
    """将数字转换为小写罗马数字"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "m", "cm", "d", "cd",
        "c", "xc", "l", "xl",
        "x", "ix", "v", "iv",
        "i"
    ]
    roman_num = ''
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syms[i]
            n -= val[i]
        i += 1
    return roman_num

if __name__ == "__main__":
    # 处理links_failed.txt或links3.txt中的失败URL
    if os.path.exists('links_failed.txt'):
        print("Processing previously failed URLs from links_failed.txt")
        process_urls(input_file='links_failed.txt')
    elif os.path.exists('links3.txt'):
        print("Processing previously failed URLs from links3.txt")
        process_urls(input_file='links3.txt')
    else:
        print("Processing all URLs from links2.txt")
        process_urls() 