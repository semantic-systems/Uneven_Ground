import os
import random
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List
import csv

from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import fitz
from io import BytesIO
import pandas as pd

def scrape_url(url) -> Tuple[str, int, List[str]]:
    all_texts = []
    try:
        r = requests.get(url, allow_redirects=False, timeout=10)

        if r.status_code == 200:
            if r.headers['Content-Type'] == 'application/pdf': # If URL is PDF
                pdf_file = BytesIO(r.content)
                doc = fitz.open(stream=pdf_file, filetype='pdf')
                all_text = ""
                for page in doc:
                    all_text += page.get_text()
                if len(all_text) > 0:
                    all_texts.append(all_text)
            else:
                soup = BeautifulSoup(r.content, 'html.parser')
                paragraphs = soup.find_all('p')
                cleaned_paragraphs = []
                for p in paragraphs:
                    for a in p.find_all('a'):
                        # a.unwrap()
                        a.replace_with(f" {a.get_text()} ")
                    cleaned_paragraphs.append(p.get_text(strip=True))
                if len(cleaned_paragraphs) > 0:
                    all_texts += cleaned_paragraphs
            return "Valid", 1, all_texts
        elif 300 <= r.status_code < 400: # If URL is redirected
            return "Redirected", 0, []
        elif r.status_code == 404: # If webpage not found
            # print(f"URL {url}. Error 404: Page not found.")
            return "Not found", 0, []
        elif r.status_code == 429:  # If webpage not found
            # print(f"URL {url}. Error 429: Too many requests.")
            print(f"URL {url}. Error 429: Too many requests.")
            return "Too many requests", 0, []
        else:
            # print(f"URL {url}. Failed to retrieve page. Status code: {r.status_code}")
            return f"Fail {r.status_code}", 0, []
    except requests.exceptions.RequestException as e:
        # print(f"URL {url}. Error fetching the url: {e}")
        return "Scraping error", 0, []


if __name__ == "__main__":
    print("[INFO] Start web scraping")

    path = "../data/"
    file = 'triples_values_urls.csv'

    df = pd.read_csv(f"{path}/{file}")
    df['url_status'] = ""
    df['is_url_valid'] = ""
    print("[INFO] Size: ", df.shape)

    if not os.path.exists(f"{path}/wiki_ref/"):
        os.makedirs(f"{path}/wiki_ref/")

    # --- Prepare jobs ---
    jobs = []
    url_to_ref = defaultdict(list)
    main_domains = set()
    for index, row in tqdm(df.iterrows()):
        output_path = f"{path}/wiki_ref/{row['RefDoc']}.txt"
        if row["URL"] not in url_to_ref:
            jobs.append(row['URL'])
        main_domains.add(row['URL'].split("/")[2])
        url_to_ref[row['URL']].append((index, row['RefDoc']))

    print("[INFO] Number of jobs: ", len(jobs))


    # --- Scrape function ---
    def scrape_job(url):
        try:
            url_status, url_validity, texts = scrape_url(url)
            return (url, url_status, url_validity, texts)
        except Exception as e:
            return (url, "Scraping error", 0, [])

    random.shuffle(jobs)


    # --- Parallel scrape and write immediately ---
    counter = 0
    with open("data/triples_values_urls_verified.csv", 'wt') as out_file:
        writer = csv.DictWriter(out_file)
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(scrape_job, url) for url in jobs]
            print("Submitted jobs")
            for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping + Writing"):
                url, url_status, url_validity, texts = future.result()

                for index, refdoc in url_to_ref[url]:
                    # Update DataFrame
                    df.at[index, 'url_status'] = url_status
                    df.at[index, 'is_url_valid'] = url_validity
                    row = df.iloc[index].to_dict()
                    writer.writerow(row)
                    if texts and not os.path.exists(f"{path}/wiki_ref/{refdoc}.txt"):
                        output_path = f"{path}/wiki_ref/{refdoc}.txt"
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(texts))



    # df.to_csv(file, sep='\t')
    print("Written " + str(counter))
