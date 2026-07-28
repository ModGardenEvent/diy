import json

import requests

import common

def ballotbox_options():
	repo_root = common.get_repo_root()
	constants_file = repo_root / "constants.jsonc"
	constants = common.jsonc_at_home(common.read_file(constants_file))

	genre_slug = constants["genre"]
	event_slug = constants["event"]
	options = []
	submissions_url = f"https://api.modgarden.net/v2/events/{genre_slug}/{event_slug}/submissions"
	print(submissions_url)
	for submission in json.loads(requests.get(submissions_url).text):
		if submission["project"]["metadata"]["type"] != "mod":
			continue
		name = submission["project"]["metadata"]["name"] if "name" in submission["project"]["metadata"] else submission["project"]["metadata"]["mod_id"]
		option = {
			"id": submission["id"],
			"mod_id": submission["project"]["metadata"]["mod_id"],
			"name": name,
			"platform": {
				"type": submission["platform"]["type"]
			}
		}

		if "description" in submission["project"]["metadata"]:
			option["description"] = submission["project"]["metadata"]["description"]
		else:
			option["description"] = f"{option['name']} has no description."

		if submission["platform"]["type"] == "modrinth":
			option["platform"]["project_id"] = submission["platform"]["project_id"]

		if "project_id" in submission["platform"] and submission["platform"]["type"] == "modrinth":
			option["platform"]["homepage_url"] = f"https://modrinth.com/project/{option['platform']['project_id']}"
		elif "source_url" in submission["project"]["metadata"]:
			option["platform"]["homepage_url"] = submission["project"]["metadata"]["source_url"]

		options.append(option)

	print(f"Writing {len(options)} submissions to options.json")
	with open(f"../pack/resources/datapack/required/mf_ballotbox/data/ballotbox/ballot/options.json", 'w', encoding="utf8") as out_file:
		json.dump(options, out_file, indent='\t')
	print("done!")


if __name__ == "__main__":
	ballotbox_options()
