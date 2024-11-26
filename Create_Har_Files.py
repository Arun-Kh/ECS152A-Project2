import time
import pandas as pd
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
import os

# Paths (update these paths)
browsermob_proxy_path = (
    "browsermob-proxy/bin/browsermob-proxy"  # Path to BrowserMob Proxy binary
)
# chromedriver_path = "/path/to/chromedriver"  # Path to ChromeDriver

# Load the list of URLs from a CSV
csv_file = "top-1m.csv"  # Your CSV file with URLs
urls_df = pd.read_csv(csv_file, usecols=[1])  # Assuming URLs are in the second column
urls = urls_df.iloc[:, 0].tolist()
urls = [
    url if url.startswith("http") else f"http://{url}" for url in urls
]  # Ensure URLs start with http/https

# Create a directory to save HAR files
output_dir = "har_files"
os.makedirs(output_dir, exist_ok=True)

# Start the BrowserMob Proxy server
server = Server(browsermob_proxy_path)
server.start()
proxy = server.create_proxy(params=dict(trustAllServers=True))

# Set up Selenium WebDriver with the proxy
chrome_options = Options()
chrome_options.add_argument(f"--proxy-server={proxy.proxy}")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(10)
# driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

# Crawl websites and capture HTTP traffic
for count, url in enumerate(urls[461:]):  # Limit to first 5 URLs for demonstration
    try:
        print(f"Crawling: {url}")
        # Start capturing a new HAR for each URL
        proxy.new_har(
            f"myhar{count}",
            options={
                "captureHeaders": True,
                "captureContent": True,
                "captureCookies": True,
            },
        )
        driver.get(url)  # Navigate to the URL
        # time.sleep(5)  # Wait for the page to load

        # Save the HAR file
        har_data = proxy.har  # Get HAR data
        sanitized_url = (
            url.replace("https://", "").replace("http://", "").replace("/", "_")
        )
        har_file_path = os.path.join(output_dir, f"{sanitized_url}.har")
        with open(har_file_path, "w") as har_file:
            json.dump(har_data, har_file)
        print(f"Saved HAR for {url} to {har_file_path}")
    except Exception as e:
        print(f"Error crawling {url}: {e}")
    # time.sleep(1)  # Delay between requests

# Clean up
driver.quit()
server.stop()
print("Crawling complete.")


# import time
# import pandas as pd
# from browsermobproxy import Server
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.proxy import Proxy, ProxyType
# import json
# import os

# # Paths (update these paths)
# # browsermob_proxy_path = "/Users/arunkhanijau/miniconda3/envs/ecs152a/lib/python3.13/site-packages/browsermobproxy/browsermob-proxy/bin/broswermob-proxy.bat"  # Path to browsermob-proxy binary
# browsermob_proxy_path = "browsermob-proxy/bin/browsermob-proxy"
# chromedriver_path = "/path/to/chromedriver"  # Path to chromedriver

# # Load the list of URLs from a CSV
# csv_file = "top-1m.csv"  # Your CSV file with URLs
# urls_df = pd.read_csv(csv_file, usecols=[1])
# urls = urls_df.iloc[:, 0].tolist()
# print(urls[:10])
# # Start the BrowserMob Proxy server
# server = Server(browsermob_proxy_path)
# server.start()
# proxy = server.create_proxy(params=dict(trustAllServers=True))

# # create a new chromedriver instance
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--proxy-server={}".format(proxy.proxy))
# chrome_options.add_argument("--ignore-certificate-errors")
# driver = webdriver.Chrome(options=chrome_options)

# # do crawling
# proxy.new_har(
#     "myhar",
#     options={"captureHeaders": True, "captureContent": True, "captureCookies": True},
# )
# count = 0
# # driver.get("http://www.cnn.com")
# for url in urls[:5]:
#     count += 1
#     try:
#         print(f"Crawling: {url}")
#         proxy.new_har(
#             "myhar" + str(count),
#             options={
#                 "captureHeaders": True,
#                 "captureContent": True,
#                 "captureCookies": True,
#             },
#         )
#         driver.get(url)
#         time.sleep(5)  # Wait for the page to load
#         har_data = proxy.har  # Get HAR data
#         har_file_path = os.path.join(
#             "har_files",
#             f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}.har",
#         )
#         with open(har_file_path, "w") as har_file:
#             har_file.write(json.dumps(proxy.har))
#     except Exception as e:
#         print(f"Error crawling {url}: {e}")
#     time.sleep(1)  # Delay between requests


# # stop server and exit
# server.stop()
# driver.quit()


# # # Set up Selenium WebDriver with the proxy
# # chrome_options = Options()
# # chrome_options.add_argument("--headless")  # Optional: Run in headless mode
# # proxy_config = Proxy(
# #     {
# #         "proxyType": ProxyType.MANUAL,
# #         "httpProxy": proxy.proxy,
# #         "sslProxy": proxy.proxy,
# #     }
# # )
# # capabilities = webdriver.DesiredCapabilities.CHROME.copy()
# # proxy_config.add_to_capabilities(capabilities)

# # service = Service(chromedriver_path)
# # driver = webdriver.Chrome(
# #     service=service, options=chrome_options, desired_capabilities=capabilities
# # )

# # # Directory to save HAR files
# # output_dir = "har_files"
# # os.makedirs(output_dir, exist_ok=True)

# # # Crawl websites and capture HTTP traffic
# # for url in urls:
# #     try:
# #         print(f"Crawling: {url}")
# #         proxy.new_har(
# #             url, options={"captureContent": True, "captureHeaders": True}
# #         )  # Start capturing
# #         driver.get(url)
# #         time.sleep(5)  # Wait for the page to load
# #         har_data = proxy.har  # Get HAR data
# #         har_file_path = os.path.join(
# #             output_dir,
# #             f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}.har",
# #         )
# #         with open(har_file_path, "w") as har_file:
# #             json.dump(har_data, har_file)
# #         print(f"Saved HAR for {url} to {har_file_path}")
# #     except Exception as e:
# #         print(f"Error crawling {url}: {e}")
# #     time.sleep(1)  # Delay between requests

# # # Cleanup
# # driver.quit()
# # server.stop()
# # print("Crawling complete. HAR files saved.")
