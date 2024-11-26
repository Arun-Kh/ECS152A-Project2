import os
import json
import tldextract
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
CONFIG = {"har_directory": "har_files", "max_workers": 4}


def is_third_party(request_url, main_domain):
    """Determine if a URL is third-party relative to the main domain."""
    extracted_url = tldextract.extract(request_url)
    extracted_main = tldextract.extract(main_domain)
    return (
        extracted_url.domain != extracted_main.domain
        or extracted_url.suffix != extracted_main.suffix
    )


def analyze_single_har(file_path):
    """Analyze a single HAR file."""
    try:
        with open(file_path, "r", encoding="utf-8") as har_file:
            har_data = json.load(har_file)
            main_domain = os.path.basename(file_path).rsplit(".har", 1)[0]
            third_party_requests = defaultdict(int)
            third_party_cookies = defaultdict(int)

            for entry in har_data.get("log", {}).get("entries", []):
                request_url = entry.get("request", {}).get("url", "")
                if request_url and is_third_party(request_url, main_domain):
                    domain = tldextract.extract(request_url).fqdn
                    third_party_requests[domain] += 1

                for cookie in entry.get("response", {}).get("cookies", []):
                    cookie_domain = cookie.get("domain", "").lstrip(".")
                    if is_third_party(cookie_domain, main_domain):
                        third_party_cookies[cookie.get("name", "")] += 1

            return main_domain, third_party_requests, third_party_cookies
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        return None, None, None


def main():
    # Collect HAR files
    har_files = [
        os.path.join(CONFIG["har_directory"], f)
        for f in os.listdir(CONFIG["har_directory"])
        if f.endswith(".har")
    ]

    # Process files in parallel
    third_party_counter = Counter()
    third_party_cookie_counter = Counter()
    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        results = executor.map(analyze_single_har, har_files)

    for main_domain, requests, cookies in results:
        if main_domain:
            for domain, count in requests.items():
                third_party_counter[domain] += count
            for cookie, count in cookies.items():
                third_party_cookie_counter[cookie] += count

    # Print results
    logging.info("\nTop 10 third-party domains:")
    for domain, count in third_party_counter.most_common(10):
        logging.info(f"{domain}: {count} requests")

    logging.info("\nTop 10 third-party cookies:")
    for cookie, count in third_party_cookie_counter.most_common(10):
        logging.info(f"{cookie}: {count} occurrences")


if __name__ == "__main__":
    main()
