import io
import json
import os
from datetime import datetime
from metadata.ci.validate.util.getsha import getsha256


def load_json_file(file_name: str) -> dict:
    with io.open(file_name, encoding="utf-8") as f:
        return json.load(f)


def update(json_, file):
    mtime = os.path.getmtime(file)
    dt = datetime.fromtimestamp(mtime)
    sha = getsha256(file)

    print(f"Updating {file} with sha256 {sha} and timestamp {dt} and mtime {mtime}")

    json_["url"] = f"https://raw.githubusercontent.com/sagarHackeD/KiCad_Plugin_Repository/refs/heads/main/{os.path.basename(file)}"
    json_["sha256"] = sha
    json_["update_timestamp"] = int(mtime)
    json_["update_time_utc"] = dt.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":

    packages = []

    for file in os.listdir("packages"):
        print(f"Processing package {file}")
        packages.append(load_json_file(os.path.join("packages", file, "metadata.json")))

    print(f"{len(packages)} packages processed")

    with io.open("packages.json", "w", encoding="utf-8") as f:
        json.dump({"packages": packages}, f, indent=4)

    repo = load_json_file("repository.json")
    repo["name"] = "sagarHackeD KiCad Plugin Repository"
    update(repo["packages"], "packages.json")

    try:
        if os.path.exists("resources.zip"):
            update(repo["resources"], "resources.zip")
        else:
            del repo["resources"]
    except KeyError:
        pass

    with io.open("repository.json", "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=4)

    print("Repository should be available at repository.json")
