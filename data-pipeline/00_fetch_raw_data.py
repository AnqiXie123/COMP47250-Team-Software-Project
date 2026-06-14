"""
00_fetch_raw_data.py
--------------------
Automatically downloads all raw data files required for the
EcoCharge Dublin pipeline.
Run this script first before any other pipeline scripts.

Data sources:
  1. ESB eCars EV charging network (data.gov.ie)
  2. EirGrid system data - wind & solar generation 2026 (eirgrid.ie)

Usage:
  python 00_fetch_raw_data.py
"""

import requests
import os

# All raw data files are saved to the raw/ folder
os.makedirs("raw", exist_ok=True)

# 1. Define data sources to download
# Each source is a dictionary with:
#   url      → download URL
#   filename → name to save as inside raw/
#   desc     → human-readable label for logging
SOURCES = [
    {
        "url": "https://cdn.esb.ie/media-staging/docs/default-source/"
               "ecars/its-data-ecars-sites/its-data-ecars-sites-roi-ni.csv",
        "filename": "its-data-ecars-sites-roi-ni.csv",
        "desc": "ESB eCars charge point locations (Ireland)"
    },
    {
        "url": "https://cms.eirgrid.ie/sites/default/files/publications/"
               "System-Data-Qtr-Hourly-2026-V4.xlsx",
        "filename": "System-Data-Qtr-Hourly-2026-V4.xlsx",
        "desc": "EirGrid system data - wind & solar 2026"
    }
]

# 2. Download function
def download_file(url, filename, desc):
    """
    Downloads a file from the given URL and saves it to raw/filename.
    Skips the download if the file already exists locally.

    Args:
        url      : the remote URL to fetch
        filename : local filename to save as (inside raw/)
        desc     : label shown in log output
    """
    filepath = os.path.join("raw", filename)

    # Skip if already downloaded
    if os.path.exists(filepath):
        print(f"[SKIP] {desc} — already exists: {filepath}")
        return

    print(f"[DOWNLOAD] {desc}")
    print(f"  URL: {url}")

    try:
        # Send an HTTP GET request
        # stream=True: the response body is downloaded in chunks
        # rather than all at once (important for large files)
        response = requests.get(url, stream=True, timeout=30)

        # Raise an error if the server returned a non-200 status code
        response.raise_for_status()

        # wb: Write the response content to disk in binary mode
        # iter_content: splits the download into 8 KB chunks
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Log the saved file size
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  Saved: {filepath} ({size_kb:.1f} KB)")

    except requests.exceptions.RequestException as e:
        # Catch the errors (net timeouts, bad status codes, etc.)
        print(f"  ERROR: {e}")


# 3. Main
if __name__ == "__main__":
    print("=" * 50)
    print("EcoCharge Dublin — Raw Data Fetcher")
    print("=" * 50)

    for source in SOURCES:
        download_file(
            url=source["url"],
            filename=source["filename"],
            desc=source["desc"]
        )

    print()
    print("Done. Raw files are in the raw/ folder.")
    print("Next step: run 01_clean_ev_chargers.py")