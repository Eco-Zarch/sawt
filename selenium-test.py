from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests
import os

URL = "https://cityofno.granicus.com/ViewPublisher.php?view_id=42"


def get_mp4_links():
    # Configure headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)

    time.sleep(10)  # Allow JS content to load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    mp4_links = []
    rows = soup.find_all("tr", class_="listingRow")

    for row in rows:
        for a in row.find_all("a", href=True):
            href = a["href"].strip()
            if ".mp4" in href:
                if href.startswith("//"):
                    href = "https:" + href
                mp4_links.append(href)

    return mp4_links


def download_file(url, filename=None):
    if not filename:
        filename = os.path.basename(url).split("?")[0]

    print(f"Downloading: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Saved as: {filename}")
    return filename


links = get_mp4_links()
if links:
    download_file(links[0])
else:
    print("No MP4 links found.")
