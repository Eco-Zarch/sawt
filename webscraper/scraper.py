from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import whisper
from time import sleep


def initialize_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


def get_mp4_links(driver, url="https://council.nola.gov/meetings/"):
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    # Switch to the iframe containing video links
    iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
    driver.switch_to.frame(iframe)

    # Retrieve all .mp4 links on the page
    mp4_elements = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '.mp4')]"))
    )
    return [element.get_attribute("href") for element in mp4_elements]


def download_video(mp4_link, save_dir="."):
    # Set the file name based on the URL
    local_filename = os.path.join(save_dir, os.path.basename(mp4_link))

    # Download the file
    response = requests.get(mp4_link, stream=True)
    with open(local_filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Video downloaded as {local_filename}")
    return local_filename


def transcribe_video(file_path):
    model = whisper.load_model("small.en")
    result = model.transcribe(file_path)
    transcription_text = result["text"]

    # Save transcription
    transcription_filename = f"{os.path.splitext(file_path)[0]}_transcription.txt"
    with open(transcription_filename, "w") as transcript_file:
        transcript_file.write(transcription_text)

    print(f"Transcription saved as {transcription_filename}")
    return transcription_filename


def process_video_by_index(index):
    driver = initialize_webdriver()

    try:
        # Step 1: Get list of mp4 links
        mp4_links = get_mp4_links(driver)

        # Validate index
        if not mp4_links or index >= len(mp4_links):
            print(f"No video found at index {index}")
            return

        # Select video link by index (older videos come first)
        mp4_link = mp4_links[index]

        # Step 2: Download the selected video
        local_video_path = download_video(mp4_link)

        # Step 3: Transcribe the video
        transcribe_video(local_video_path)

    finally:
        driver.quit()


# Using index 0 to process the oldest video
for i in range(2, 5):
    process_video_by_index(i)
    sleep(10)
