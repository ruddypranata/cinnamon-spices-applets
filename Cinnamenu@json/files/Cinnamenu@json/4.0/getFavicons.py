#! /usr/bin/python3


import os
import sys
import tempfile
import shutil
import sqlite3
import json
import urllib.parse

FAVICON_CACHE_DIR = os.path.join(os.path.split(__file__)[0], "../favicon_cache")

# Params: sqlite_file: path to Favicons file from which to extract favicons
#        domains_list: list of domains to find favicons for eg. ["https://google.com","http:/..."]
# return: domains with a path to icon eg. {"https://google.com": "/home/USER/.local/share/cinnamon/applets/Cinnamen@json/favicons_cache/google.com", "https://...": "..."}
def get_favicons(sqlite_file, domains_list):
    if not os.path.exists(FAVICON_CACHE_DIR):
        os.mkdir(FAVICON_CACHE_DIR)

    #make temp copy of Favicons file as orignal may be locked.
    fd, temp_filename = tempfile.mkstemp()
    os.close(fd)
    shutil.copyfile(sqlite_file, temp_filename)

    conn = sqlite3.Connection(temp_filename)
    cur = conn.cursor()

    domains_to_favicons = {}
    for domain in domains_list:
        cur.execute("SELECT id, url FROM favicons WHERE url LIKE ?", [domain + "%"])

        for favicon_id, url in cur.fetchall():
            url_parsed = urllib.parse.urlparse(domain)
            netloc = url_parsed.netloc
            filename = os.path.join(FAVICON_CACHE_DIR, netloc)
            if not os.path.exists(filename):
                cur2 = conn.cursor()
                cur2.execute("SELECT icon_id, image_data FROM favicon_bitmaps WHERE icon_id = ?", (favicon_id, ))
                #There are usually 2 results, a 16px and a 32px PNG with the 32px being the second result.
                #Save both to same filename so that the 32px overwrites the 16px
                for icon_id, image_data in cur2.fetchall():
                    image_file = open(filename, "w+b")
                    image_file.write(image_data)
                cur2.close()
            if os.path.exists(filename):
                domains_to_favicons[domain] = filename

    cur.close()
    os.unlink(temp_filename)

    return domains_to_favicons

if __name__ == "__main__":
    if len(sys.argv) > 2:
        sqlite_file = sys.argv[1]
        domains_json = sys.argv[2]
        domains_list = json.loads(domains_json)
        results = get_favicons(sqlite_file, domains_list)
        print(json.dumps(results))
