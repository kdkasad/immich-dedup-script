#!/usr/bin/env python3

import requests
import requests.auth

# Base URL without trailing slash
base_url = ""

ERROR_MARKER = "\n\x1b[1;31m !\x1b[m"


def main():
    global base_url

    with open("base_url.txt", "r") as file:
        base_url = file.read().strip()

    session = requests.Session()
    session.auth = getAuth()

    # Get duplicates
    r = session.get(base_url + "/api/duplicates")
    duplicates = r.json()

    stackList = []
    dedupList = []
    for duplicate in duplicates:
        assets = duplicate["assets"]

        if allSameKey("checksum", assets):
            dedupList.append(duplicate)

        if (
            allSameKey("originalFileName", assets, transform=str.lower)
            and allSameKey(["exifInfo", "exifImageWidth"], assets)
            and allSameKey(["exifInfo", "exifImageHeight"], assets)
        ):
            dedupList.append(duplicate)

        if isRawPair(assets):
            stackList.append(duplicate)

    print(
        f"Will deduplicate {len(dedupList)} duplicates and stack {len(stackList)} raw pairs."
    )
    print("Continue? (y/n) ", end="")
    if input().strip().lower() != "y":
        print("Aborted.")
        return

    done = 0
    total = len(dedupList)
    for duplicate in dedupList:
        done += 1
        print(f"\rDeduplicating... {done}/{total}", end="")
        deduplicate(session, duplicate)
    print()

    done = 0
    total = len(stackList)
    for duplicate in stackList:
        done += 1
        print(f"\rStacking... {done}/{total}", end="")
        stack(session, duplicate)
    print()


def isRawPair(assets):
    if len(assets) != 2:
        return False
    extensions = sorted(
        map(lambda a: a["deviceAssetId"].split(".")[-1].lower(), assets)
    )
    rawPairs = [
        ["cr2", "jpg"],
        ["jpg", "orf"],
        ["jpg", "psd"],
    ]
    return extensions in rawPairs


def deduplicate(session, duplicate):
    assets = sorted(
        duplicate["assets"], key=lambda a: a["exifInfo"]["fileSizeInByte"], reverse=True
    )
    try:
        session.delete(
            base_url + "/api/assets",
            json={
                "ids": [a["id"] for a in assets[1:]],
            },
        ).raise_for_status()
    except requests.RequestException as e:
        print(
            ERROR_MARKER, f"Failed to delete assets for {duplicate['duplicateId']}: {e}"
        )
        return
    try:
        session.put(
            base_url + "/api/assets",
            json={
                "duplicateId": None,
                "ids": [assets[0]["id"]],
            },
        ).raise_for_status()
    except requests.RequestException as e:
        print(
            ERROR_MARKER, f"Failed to delete duplicate {duplicate['duplicateId']}: {e}"
        )


def stack(session, duplicate):
    try:
        session.post(
            base_url + "/api/stacks",
            json={
                "assetIds": [a["id"] for a in duplicate["assets"]],
            },
        ).raise_for_status()
    except requests.RequestException as e:
        print(
            ERROR_MARKER, f"Failed to stack assets for {duplicate['duplicateId']}: {e}"
        )
        return
    try:
        session.put(
            base_url + "/api/assets",
            json={
                "duplicateId": None,
                "ids": [asset["id"] for asset in duplicate["assets"]],
            },
        ).raise_for_status()
    except requests.RequestException as e:
        print(
            ERROR_MARKER, f"Failed to delete duplicate {duplicate['duplicateId']}: {e}"
        )


def allSameKey(key, values, transform=lambda s: s):
    def getKeyValue(item, key):
        if type(key) is str:
            return transform(item[key])
        elif type(key) is list:
            for k in key:
                item = item[k]
            return transform(item)

    for i in range(1, len(values)):
        if getKeyValue(values[i], key) != getKeyValue(values[0], key):
            return False
    return True


class ImmichAPIKeyAuth(requests.auth.AuthBase):
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, r):
        r.headers["x-api-key"] = self.api_key
        return r


def getAuth() -> ImmichAPIKeyAuth:
    with open("api_key.txt", "r") as file:
        api_key = file.read().strip()
    return ImmichAPIKeyAuth(api_key)


if __name__ == "__main__":
    main()
