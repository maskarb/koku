from os import environ

import requests

if __name__ == "__main__":
    koku_host = environ.get("KOKU_API_HOSTNAME")
    koku_port = environ.get("KOKU_PORT")
    url = f"http://{koku_host}:{koku_port}/api/cost-management/v1/sources/"

    r = requests.get(url).json()
    source_uuids = []
    source_uuids.extend(
        source_uuid
        for source in r.get("data", [])
        if (source_uuid := source.get("uuid"))
    )

    for source_uuid in source_uuids:
        delete_url = f"{url}{source_uuid}/"
        print(f"Calling {delete_url}")
        r = requests.delete(delete_url)
        print(r)
