import os
import re
import zipfile
import subprocess
import sys

DIFF_FILE = "artifacts/diff_files.txt"
PACKAGES_DIR = "packages"
BUILD_SCRIPT = "ci/build-repository.py"


# --------------------------------------------------
# Read diff file
# --------------------------------------------------
if not os.path.exists(DIFF_FILE):
    print("diff file not found:", DIFF_FILE)
    sys.exit(1)

with open(DIFF_FILE, encoding="utf-8") as f:
    lines = f.readlines()


# --------------------------------------------------
# Extract changed metadata + icon files
# --------------------------------------------------
metadata_files = []
icon_files = []

meta_pattern = re.compile(r'^[AM]\s+(packages/[^/]+/metadata\.json)$')
icon_pattern = re.compile(r'^[AM]\s+(packages/[^/]+/icon\.png)$')

for line in lines:
    line = line.strip()

    m = meta_pattern.match(line)
    if m:
        metadata_files.append(m.group(1))
        continue

    m = icon_pattern.match(line)
    if m:
        icon_files.append(m.group(1))


# --------------------------------------------------
# Add icons for changed metadata
# --------------------------------------------------
for f in metadata_files.copy():
    icon = os.path.join(os.path.dirname(f), "icon.png")
    if os.path.exists(icon) and icon not in icon_files:
        icon_files.append(icon)


# --------------------------------------------------
# Add metadata for changed icons
# --------------------------------------------------
for f in icon_files.copy():
    metadata = os.path.join(os.path.dirname(f), "metadata.json")
    if metadata not in metadata_files:
        metadata_files.append(metadata)


# --------------------------------------------------
# Create resources.zip
# --------------------------------------------------
if icon_files:
    os.makedirs("artifacts", exist_ok=True)

    zip_path = "artifacts/resources.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in icon_files:
            rel = re.sub(r"^packages/", "", f)
            z.write(f, rel)

    print("Created:", zip_path)


# --------------------------------------------------
# Run repository builder
# --------------------------------------------------
if metadata_files:
    print("\nGenerating repo with following packages:")

    for f in metadata_files:
        print(" ", f.split("/")[1])

    cmd = [sys.executable, BUILD_SCRIPT] + metadata_files

    print("\nRunning:", " ".join(cmd))
    subprocess.run(cmd, check=True)
else:
    print("No changed metadata files.")