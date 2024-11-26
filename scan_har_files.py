import os
import json
import tldextract
from collections import defaultdict, Counter


def is_third_party(request_url, main_domain):
    """
    Check if the request URL belongs to a third-party domain.
    """
    extracted_url = tldextract.extract(request_url)
    extracted_main = tldextract.extract(main_domain)

    # A third-party domain has a different domain name or suffix.
    return (
        extracted_url.domain != extracted_main.domain
        or extracted_url.suffix != extracted_main.suffix
    )


def get_main_domain_from_filename(file_name):
    """
    Extract the main domain from the file name (e.g., 'example.com.har').
    """
    if file_name.endswith(".har"):
        return file_name.rsplit(".har", 1)[0]
    return ""


def analyze_har_files(directory):
    """
    Process all HAR files in the given directory and track third-party requests.
    """
    third_party_requests_summary = defaultdict(lambda: defaultdict(int))
    global_third_party_counter = Counter()

    for file_name in os.listdir(directory):
        if file_name.endswith(".har"):
            main_domain = get_main_domain_from_filename(file_name)
            if not main_domain:
                print(f"Skipping file with invalid name format: {file_name}")
                continue

            har_file_path = os.path.join(directory, file_name)
            with open(har_file_path, "r", encoding="utf-8") as har_file:
                try:
                    har_data = json.load(har_file)
                    entries = har_data.get("log", {}).get("entries", [])

                    for entry in entries:
                        request_url = entry.get("request", {}).get("url", "")
                        if request_url and is_third_party(request_url, main_domain):
                            extracted = tldextract.extract(request_url)
                            domain = f"{extracted.domain}.{extracted.suffix}"
                            third_party_requests_summary[main_domain][domain] += 1
                            global_third_party_counter[domain] += 1

                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {file_name}")

    return third_party_requests_summary, global_third_party_counter


def main():
    # Directory containing HAR files
    har_directory = input(
        "Enter the path to the directory containing HAR files: "
    ).strip()

    # Analyze HAR files
    third_party_requests_summary, global_third_party_counter = analyze_har_files(
        har_directory
    )

    # Output results for each main domain
    for main_domain, third_party_requests in third_party_requests_summary.items():
        print(f"\nThird-party requests for {main_domain}:")
        for domain, count in sorted(
            third_party_requests.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {domain}: {count} requests")

    # Output the top 10 most common third-party domains
    print("\nTop 10 most common third-party domains across all files:")
    for domain, count in global_third_party_counter.most_common(10):
        print(f"{domain}: {count} requests")


if __name__ == "__main__":
    main()
