from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import pandas as pd
import time
import os
import glob
from selenium.webdriver.common.by import By
import shutil

import re

def sanitize_filename(filename):
    # Remove invalid characters
    s = re.sub(r'[\/:*?"<>|]', '_', filename)
    # Truncate long filenames
    max_length = 240  # Change as needed; 240 allows for file extension and some path on most file systems
    return s[:max_length]


def read_ris(path):
    # open as txt file
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # split into rows
    rows = text.split('\n')
    # retain rows that start with "DO  - "
    doi_rows = [row for row in rows if row.startswith('DO  - ')]
    # remove "DO  - "
    doi_rows = [row[6:] for row in doi_rows]
    title_rows = [row for row in rows if row.startswith('TI  - ')]
    title_rows = [sanitize_filename(row[6:].strip()) for row in title_rows]

    doi_title_tuples = [(doi, title) for doi, title in zip(doi_rows, title_rows)]

    return doi_title_tuples



def check_scihub(driver, url):
    if 'sci-hub' not in driver.page_source:
        # wait for 20 seconds
        print("Possible blank page. Waiting for 20 seconds.")
        time.sleep(20)
        # check again
        driver.get(url)
        check_scihub(driver, url)
    else:
        pass


def process_dois(doi_title_tuples, destination_path, downloads_url):
    options = webdriver.FirefoxOptions()

    options.add_argument('--no-sandbox')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0')
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))

    counter = 0
    for (doi, title) in doi_title_tuples:
        if counter % 50 == 0 and counter != 0:
            driver.quit()
            time.sleep(40)
            options = webdriver.FirefoxOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101 Firefox/10.0')
            driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
        if os.path.exists(os.path.join(destination_path, title + '.pdf')):
            continue
        else:
            counter += 1

            url = 'https://sci-hub.se/' + doi
            driver.get(url)
            time.sleep(2)
            # check if "scihub" is on the page
            check_scihub(driver, url)

            try:
                button = driver.find_element(By.XPATH, '//button[text()="↓ save"]')
                button.click()
                # Switch to the new tab
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(2)
                # Close the new tab
                driver.close()
                driver.switch_to.window(driver.window_handles[0])


                # list all files in the directory
                files = glob.glob(os.path.join(downloads_url, "*"))

                # find the most recently downloaded file
                latest_file = max(files, key=os.path.getctime)

                # move the file to the save path
                shutil.move(latest_file, os.path.join(destination_path, title + '.pdf'))
            except:
                print("Could not download: " + title)
                continue

    files = os.listdir(destination_path)
    downloaded_successfully = [True if title + '.pdf' in files else False for (doi, title) in doi_title_tuples]


    # to pandas
    df = pd.DataFrame({'doi': [doi for (doi, title) in doi_title_tuples],
                       'title': [title for (doi, title) in doi_title_tuples],
                       'downloaded_successfully': downloaded_successfully})
    # save
    df.to_csv(os.path.join(destination_path, 'downloaded_successfully.csv'), index=False)


    driver.quit()

# make program
def main():
    # get path to ris file
    path = r"C:\Users\hplis\OneDrive\Desktop\PHD\readings\emotions\scopus.ris"
    # read ris file
    doi_title_tuples = read_ris(path)
    # get destination path
    destination_path = r"C:\Users\hplis\OneDrive\Desktop\PHD\readings\emotions"
    # process dois
    downloads_url = r'C:\Users\hplis\Downloads'

    process_dois(doi_title_tuples, destination_path, downloads_url)


# run program
if __name__ == '__main__':
    main()