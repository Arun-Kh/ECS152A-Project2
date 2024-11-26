import os
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
CONFIG = {
    "browsermob_proxy_path": "browsermob-proxy/bin/browsermob-proxy",
    "output_dir": "har_files",
    "csv_file": "top-1m.csv",
    "max_workers": 4,
    "page_load_timeout": 10,
    "headless": True,
}

# Setup proxy and driver creation with threading lock
lock = threading.Lock()


def setup_proxy_and_driver():
    """Setup BrowserMob Proxy and Selenium WebDriver."""
    server = Server(CONFIG["browsermob_proxy_path"])
    server.start()
    proxy = server.create_proxy(params={"trustAllServers": True})

    chrome_options = Options()
    chrome_options.add_argument(f"--proxy-server={proxy.proxy}")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    if CONFIG["headless"]:
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(CONFIG["page_load_timeout"])
    return server, proxy, driver


def cleanup(server, driver):
    """Stop proxy server and quit WebDriver."""
    if driver:
        driver.quit()
    if server:
        server.stop()


def crawl_and_save_har(url, count):
    """Crawl a URL and save its HAR file."""
    server, proxy, driver = None, None, None
    try:
        logging.info(f"Processing URL {count}: {url}")
        server, proxy, driver = setup_proxy_and_driver()

        proxy.new_har(
            f"site{count}",
            options={
                "captureHeaders": True,
                "captureContent": True,
                "captureCookies": True,
            },
        )
        driver.get(url)

        har_data = proxy.har
        sanitized_url = (
            url.replace("https://", "").replace("http://", "").replace("/", "_")
        )
        output_path = os.path.join(CONFIG["output_dir"], f"{sanitized_url}.har")

        with lock:
            with open(output_path, "w") as har_file:
                json.dump(har_data, har_file)
        logging.info(f"Saved HAR file for {url}")
    except TimeoutException:
        logging.error(f"Timeout loading {url}")
    except WebDriverException as e:
        logging.error(f"WebDriver error with {url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error with {url}: {e}")
    finally:
        cleanup(server, driver)


def main():
    # Load URLs
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    urls_df = pd.read_csv(CONFIG["csv_file"], usecols=[1])
    urls = [
        url if url.startswith("http") else f"http://{url}" for url in urls_df.iloc[:, 0]
    ]

    # Process in parallel
    with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
        for count, url in enumerate(urls[:100]):  # Limit for demo
            executor.submit(crawl_and_save_har, url, count)


if __name__ == "__main__":
    main()
