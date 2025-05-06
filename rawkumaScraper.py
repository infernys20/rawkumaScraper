import requests
from bs4 import BeautifulSoup
import subprocess
import time

url = input('Paste rawkuma link, e.g. https://rawkuma.net/manga/sousou-no-frieren/: ')
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'
}

# Get the manga page
r = requests.get(url=url, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')

# Iterate over each chapter element
for chapter in soup.find_all('li', {'data-num': True}):
    chapter_number = chapter['data-num']
    manga_name = url.replace('https://rawkuma.net/manga/', '').strip('/')
    download_page = chapter.select_one('a.dload')['href']

    print(f"Resolving download for chapter {chapter_number}...")

    # Follow redirect from the rawkuma download page
    session = requests.Session()
    dl_response = session.get(download_page, headers=headers, allow_redirects=False)

    if dl_response.status_code == 302 or dl_response.status_code == 303:
        google_drive_url = dl_response.headers['Location']
    else:
        print(f"Failed to get redirect from {download_page}")
        continue

    # Follow redirect from Google Drive to final file
    g_response = session.get(google_drive_url, headers=headers, allow_redirects=False)
    if 'Location' in g_response.headers:
        final_url = g_response.headers['Location']
    else:
        print(f"Failed to get final download URL from Google Drive for chapter {chapter_number}")
        continue

    filename = f"{manga_name}-ch{chapter_number}.zip"
    print(f"Downloading {final_url} as {filename}...")

    # Download the file via wget
    subprocess.run(["wget", "--content-disposition", "-O", filename, final_url])
    time.sleep(5)

print("All downloads completed.")
