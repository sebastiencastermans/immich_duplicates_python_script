"""
🧹 Immich duplicate cleanup script
-----------------------------------------

This script was developed by Sébastien Castermans, with the help of AI, to identify and retain
the best version of duplicate files (photos/videos) on an Immich server via its API.
It allows you to efficiently delete duplicates based on criteria such as creation date, HEIC
format (Apple original), file size, and EXIF metadata.
The duplicate detection setting is specific to your Immich installation and can be modified
in the server's administration settings.

💡 Features :
- Intelligent sorting to keep the best version of a file, first the oldest, then priority to
HEIC files (Apple originals), otherwise according to size, and finally EXIF metadata.
- Simulation option (dry run) to test without deleting
- Delete to recycle bin or permanently delete
- Detailed logging to a .log file if enabled
- Ability to view files with their URLs in the logs

Improvements welcome! Feel free to share with attribution.
"""


import requests
import json
from datetime import datetime
import sys

# User configuration:
ENABLE_LOG_FILE = True # True = creates an immich_duplicates.log file, False = no log file
SERVER = "https://immich.example.com"  # Replace with the URL of your Immich server or, failing that, the IP address.
API_KEY = "ENTER_YOUR_API_KEY_HERE" # Replace with your Immich API key
DRY_RUN = True  # True = only simulates to see the selected files in the output, does not actually delete them
# Set to False to actually delete duplicates
DEFINITELY = False  # True = permanently deleted, False = in the recycle bin



if ENABLE_LOG_FILE:
    log_filename = f"immich_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, message):
            for stream in self.streams:
                stream.write(message)
                stream.flush()
        def flush(self):
            for stream in self.streams:
                stream.flush()
    logfile = open(log_filename, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.stdout, logfile)
    sys.stderr = Tee(sys.stderr, logfile)

# Step 1: Retrieve duplicates
HEADERS = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}
try:
    response = requests.get(f"{SERVER}/api/duplicates", headers=HEADERS)
    response.raise_for_status()
    duplicates = response.json()
except requests.RequestException :
    print(f"[ERROR] Failed to retrieve duplicates, server {SERVER} unreachable or invalid API key.")
    exit(1)
if not duplicates:
    print("[INFO] No duplicates found. Nothing to delete.")
    exit(0)


# Step 2: Prepare the files to be deleted
def get_asset_info(asset):
    exif = asset.get('exifInfo', {})
    try:
        date = datetime.fromisoformat(exif.get('dateTimeOriginal'))
    except (ValueError, TypeError):
        date = datetime.max  # Worst date if empty
    is_heic = 1 if asset['originalFileName'].lower().endswith('.heic') else 0
    size = exif.get('fileSizeInByte')
    exif_count = sum(1 for v in exif.values() if v is not None and (not isinstance(v, str) or v.strip() != ""))
    return (date, is_heic, size, exif_count)

def select_best_asset(assets):
    remaining = assets[:]
    length = len(remaining)
    reason = "identical files with the criteria (date, heic, size, exif)"

    # Step 1: Earliest date
    min_date = min(get_asset_info(a)[0] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[0] == min_date]
    if len(remaining) == 1:
        reason = "older"
        return remaining[0], reason
    if length != len(remaining):
        reason = "older"
        length = len(remaining)

    # Step 2: Priority to .heic
    heic = max(get_asset_info(a)[1] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[1] == heic]
    if len(remaining) == 1:
        reason = "heic extension"
        return remaining[0], reason
    if length != len(remaining):
        reason = "heic extension"
        length = len(remaining)

    # Step 3: larger size
    max_size = max(get_asset_info(a)[2] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[2] == max_size]
    if len(remaining) == 1:
        reason = "larger size"
        return remaining[0], reason
    if length != len(remaining):
        reason = "larger size"
        length = len(remaining)

    # Step 4: More EXIF fields
    max_exif = max(get_asset_info(a)[3] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[3] == max_exif]
    if len(remaining) == 1:
        reason = "more exif data"
        return remaining[0], reason
    if length != len(remaining):
        reason = "more exif data"
        length = len(remaining)

    # Final equality
    return remaining[0], reason


ids_to_delete = []
i = 0
for group in duplicates:
    i = i + 1
    assets = group.get('assets')
    kept, reason = select_best_asset(assets)
    date, is_heic, size, exif_count = get_asset_info(kept)
    date_str = date.strftime('%d/%m/%y - %H:%M:%S') if date != datetime.max else "??/??/??"
    print(f"\n[INFO] Duplicates n°{i} ({len(assets)} files), conservation reason : '{reason}'")
    print(f"[KEPT]\t\tDate : {date_str}\tSize : {round(size/1024/1024,2)}MB\t\tNumber of EXIF : {exif_count}\t{kept['originalFileName']} --> {SERVER}/api/assets/{kept['id']}/thumbnail?size=preview")
    for asset in assets:
        if asset['id'] != kept['id']:
            date, is_heic, size, exif_count = get_asset_info(asset)
            date_str = date.strftime('%d/%m/%y - %H:%M:%S') if date != datetime.max else "??/??/??"
            print(f"[DELETED]\tDate : {date_str}\tSize : {round(size/1024/1024,2)}MB\t\tNumber of EXIF : {exif_count}\t{asset['originalFileName']} --> {SERVER}/api/assets/{asset['id']}/thumbnail?size=preview")
            ids_to_delete.append(asset['id'])


# Step 3: Remove duplicates via the API
if DRY_RUN:
    print("\n[INFO] Simulation mode enabled. No actual deletion performed.")
    exit(0)

HEADERS = {
  'Content-Type': 'application/json',
  'x-api-key': API_KEY
}
PAYLOAD = json.dumps({"force": DEFINITELY, "ids": ids_to_delete})
try:
    delete_response = requests.delete(f"{SERVER}/api/assets", headers=HEADERS, data=PAYLOAD)
    delete_response.raise_for_status()
    print(f"\n[SUCCESS] Deletion successful.")
except requests.RequestException:
    print(f"\n[ERROR] Deletion failed : {delete_response.status_code} is the HTTP status code returned.")
    print(f"[DEBUG] API response : {delete_response.text if 'delete_response' in locals() else 'none'}")
