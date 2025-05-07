import requests
from bs4 import BeautifulSoup
import subprocess
import time
import os

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

    filename = f"{manga_name}-ch{chapter_number}.zip"

    if os.path.exists(filename):
        print(f"Skipping chapter {chapter_number}, file already exists: {filename}")
        continue

    print(f"Resolving download for chapter {chapter_number}...")

    session = requests.Session()
    session.headers.update(headers)

    # Get redirected to Google Drive link
    dl_response = session.get(download_page, allow_redirects=False)

    # Handle archive isn't ready yet
    if dl_response.status_code == 200:

        if 'continue=1' not in download_page:
            print("Archive not ready, waiting...")
            if '?' in download_page:
                download_page += '&continue=1'
            else:
                download_page += '?continue=1'

            dl_response = session.get(download_page, allow_redirects=False)

    # Handle download nornally
    if dl_response.status_code in (302, 303):
        google_drive_url = dl_response.headers['Location']
    else:
        print(f"Failed to get redirect from {download_page}")
        continue

    # Check if it's a virus warning page
    g_response = session.get(google_drive_url)

    if 'Content-Disposition' in g_response.headers:
        final_url = g_response.url

    elif "Google Drive can't scan this file for viruses" in g_response.text:
        soup = BeautifulSoup(g_response.text, 'html.parser')
        form = soup.find('form', {'id': 'download-form'})

        if form:
            action_url = form['action']
            params = {
                inp['name']: inp['value']
                for inp in form.find_all('input') if inp.has_attr('name')
            }
            final_url = requests.Request('GET', action_url, params=params).prepare().url
        else:
            print(f"Failed to extract confirmation form for chapter {chapter_number}")
            continue
    else:
        print(f"Unexpected response for chapter {chapter_number}")
        continue

    print(f"Downloading {filename} from {final_url}...")
    subprocess.run(["wget", "--content-disposition", "-O", filename, final_url])
    time.sleep(5)

print("All downloads completed.")
