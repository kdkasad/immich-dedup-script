# Immich deduplication script

Makes decisions on what to do with images identified as duplicates by Immich.

Retrieves sets of images listed as duplicates from Immich, then does the following:
- If the images have the same checksum, then one is kept and the rest are deleted.
- If the set has two images, one with extension `.jpg` and one with either `.cr2`, `.orf`, or `.psd`, then the images are stacked and neither is deleted.
- If all images in the set have the same name and dimensions, then the largest (by file size) is kept and the rest are deleted.

# Usage

1. Create an Immich API key for your user with the following permissions:
   - `asset.read`
   - `asset.update`
   - `asset.view`
   - `asset.delete`
   - `stack.create`
2. Write the API key to a file named `api_key.txt` in the same directory as the script.
3. Write the URL of your Immich instance (without a trailing slash) to `base_url.txt`.
4. `uv run main.py`
