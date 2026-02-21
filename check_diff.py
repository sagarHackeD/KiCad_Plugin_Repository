import os
import re
import sys
import subprocess
import urllib.request

# --------------------------------------------------
# ENV INPUTS (same as bash variables)
# --------------------------------------------------

DIFF_FILES = os.environ.get("DIFF_FILES", "")
SCHEMA_URL = os.environ.get(
    "SCHEMA_URL",
    "https://gitlab.com/kicad/code/kicad/-/raw/master/kicad/pcm/schemas/pcm.v1.schema.json"
)
MERGE_BASE_SHA = os.environ.get("MERGE_BASE_SHA", "")

# --------------------------------------------------
# Write diff file
# --------------------------------------------------

os.makedirs("artifacts", exist_ok=True)

diff_path = "artifacts/diff_files.txt"
with open(diff_path, "w", encoding="utf-8") as f:
    f.write(DIFF_FILES)

if not DIFF_FILES.strip():
    print("No changed files")
    sys.exit(0)

print("Changed files")
print(DIFF_FILES)


lines = DIFF_FILES.splitlines()

# --------------------------------------------------
# Helper regex filters
# --------------------------------------------------

def match(pattern):
    r = re.compile(pattern)
    return [l for l in lines if r.search(l)]


def extract_path(lines):
    return [l.split(maxsplit=1)[1] for l in lines]


# --------------------------------------------------
# Check for spaces in packages
# --------------------------------------------------

spaces = match(r'^.\s+packages\/[^/]* [^/]*/')

if spaces:
    print("Spaces are not allowed in package names")
    sys.exit(1)


# --------------------------------------------------
# Don't allow deleted metadata
# --------------------------------------------------

deleted = match(r'^D\s+packages\/[^/]+/metadata\.json$')

if deleted:
    print("Deleting package metadata files is not allowed, to delist a package remove all versions.")
    sys.exit(1)


# --------------------------------------------------
# Download schema
# --------------------------------------------------

print("Downloading schema...")

try:
    urllib.request.urlretrieve(SCHEMA_URL, "schema.json")
except Exception as e:
    print("Failed to download schema:", e)
    sys.exit(1)


# --------------------------------------------------
# Validate NEW packages
# --------------------------------------------------

new_meta = extract_path(match(r'^A\s+packages\/[^/]+/metadata\.json$'))

for f in new_meta:
    package = f.split("/")[1]
    print(f"Validating new package {package}")

    result = subprocess.run(
        [sys.executable, "ci/validate-package.py", package, f]
    )

    if result.returncode != 0:
        print(f"Validation of package {package} failed")
        sys.exit(1)


# --------------------------------------------------
# Validate CHANGED packages
# --------------------------------------------------

changed_meta = extract_path(match(r'^M\s+packages\/[^/]+/metadata\.json$'))

for f in changed_meta:
    package = f.split("/")[1]
    old_file = f + ".old"

    print(f"Validating changes to package {package}")

    with open(old_file, "w", encoding="utf-8") as out:
        subprocess.run(
            ["git", "show", f"{MERGE_BASE_SHA}:{f}"],
            stdout=out,
            check=True
        )

    result = subprocess.run(
        [sys.executable, "ci/validate-package.py", package, f, old_file]
    )

    if result.returncode != 0:
        print(f"Validation of package {package} failed")
        sys.exit(1)


# --------------------------------------------------
# Validate icons
# --------------------------------------------------

icon_files = extract_path(match(r'^[MA]\s+packages\/[^/]+/icon\.png$'))

for f in icon_files:
    package = f.split("/")[1]
    print(f"Validating icon {f}")

    result = subprocess.run(
        [sys.executable, "ci/validate-image.py", f]
    )

    if result.returncode != 0:
        print(f"Validation of icon for package {package} failed")
        sys.exit(1)


print("Done")