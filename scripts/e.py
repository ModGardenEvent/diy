#!/usr/bin/env python3
import json

import requests

import common
from common import Ansi


def get_name_user(user_id):
    user = json.loads(requests.get(f"https://api.modgarden.net/v2/users/{user_id}").text)
    return user["bio"]["display_name"] if user["bio"]["display_name"] is not None else user["username"]

def main():
    modrinth_api = "https://api.modrinth.com/v2"
    repo_root = common.get_repo_root()
    constants_file = repo_root / "constants.jsonc"
    submissions_file = repo_root / "submissions.json"
    submission_lock_file = repo_root / "submissions-lock.json"
    packwiz_pack_toml = repo_root / "pack" / "pack.toml"
    packwiz = common.check_packwiz()
    
    common.fix_packwiz_pack(packwiz_pack_toml)

    constants = common.jsonc_at_home(common.read_file(constants_file))
    
    # Download the json
    genre_slug = constants["genre"]
    event_slug = constants["event"]
    if event_slug is None or genre_slug is None:
        print(f"{Ansi.WARN}No event or genre slug defined. Treating it as if there were zero submissions{Ansi.RESET}")
        print(f"Was this unintentional? Check {constants_file.relative_to(repo_root)} and make sure it defines \"event\" and \"genre\"")
        submission_data = []
    else:
        submissions_url = f"https://api.modgarden.net/v2/events/{genre_slug}/{event_slug}/submissions"
        submission_data = json.loads(requests.get(submissions_url).text)

    credits = []
    for s in submission_data:
        if s["project"]["metadata"]["type"] == "mod":
            credits.append({
                "title": s["project"]["metadata"]["name"] if s["project"]["metadata"]["name"] is not None else s["project"]["metadata"]["mod_id"],
                "names": map(get_name_user, s["team"].keys())
            })
    print(json.dumps(credits))

if __name__ == "__main__":
    main()
