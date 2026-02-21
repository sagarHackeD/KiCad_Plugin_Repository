import hashlib
import json
import os
from datetime import datetime
import zipfile

READ_SIZE = 65536


def getsha256(filename) -> str:
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        while data := f.read(READ_SIZE):
            sha256.update(data)
    return sha256.hexdigest()


def load_json_file(file_name: str) -> dict:
    with open(file_name, encoding="utf-8") as f:
        return json.load(f)


def update(json_, file):
    mtime = os.path.getmtime(file)
    dt = datetime.fromtimestamp(mtime)
    sha = getsha256(file)

    print(f"Updating {file} with sha256 {sha} and timestamp {dt} and mtime {mtime}")

    json_["url"] = (
        f"https://raw.githubusercontent.com/sagarHackeD/KiCad_Plugin_Repository/refs/heads/main/{os.path.basename(file)}"
    )
    json_["sha256"] = sha
    json_["update_timestamp"] = int(mtime)
    json_["update_time_utc"] = dt.strftime("%Y-%m-%d %H:%M:%S")


def create_resources_zip(icon_files):
    if not icon_files:
        return

    with zipfile.ZipFile(
        "resources.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as z:
        for path in icon_files:
            z.write(path, os.path.relpath(path, "packages"))


if __name__ == "__main__":
    packages = []

    for file in os.listdir("packages"):
        print(f"Processing package {file}")
        packages.append(load_json_file(os.path.join("packages", file, "metadata.json")))

    print(f"{len(packages)} packages processed")

    with open("packages.json", "w", encoding="utf-8") as f:
        json.dump({"packages": packages}, f, indent=4)

    repo = load_json_file("repository.json")
    repo["name"] = "sagarHackeD KiCad Plugin Repository"
    update(repo["packages"], "packages.json")

    create_resources_zip(
        [
            os.path.join("packages", file, "icon.png")
            for file in os.listdir("packages")
            if os.path.exists(os.path.join("packages", file, "icon.png"))
        ]
    )

    try:
        if os.path.exists("build/resources.zip"):
            update(repo["resources"], "build/resources.zip")
        else:
            del repo["resources"]
    except KeyError:
        pass

    with open("repository.json", "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=4)
