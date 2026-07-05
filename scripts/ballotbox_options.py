import json

import requests


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
		option = {
			"id": submission["id"],
			"mod_id": submission["project"]["metadata"]["mod_id"],
			# "name": submission["name"],
			# "description": submission["description"],
			"platform": {
				"type": submission["platform"]["type"]
			}
			"project": {}
		}
		if submission["project"]["metadata"]["name"] is not None:
			option["project"]["name"] = submission["project"]["metadata"]["name"]
		else
			option["project"]["name"] = option["mod_id"]

		if submission["project"]["metadata"]["description"] is not None:
			option["description"] = submission["project"]["metadata"]["description"]
		else
			option["description"] = f"{option["project"]["name"]} has no description."

		if submission["platform"]["type"] == "modrinth":
			option["project"]["modrinth_id"] = submission["platform"]["project_id"]

		if "source_url" in submission["project"]["metadata"]:
			option["platform"]["homepage_url"] = submission["project"]["metadata"]["source_url"]

		options.append(option)

	print(f"Writing {len(options)} submissions to options.json")
	with open(f"../pack/resources/datapack/required/mf_ballotbox/data/ballotbox/ballot/options.json", 'w', encoding="utf8") as out_file:
		json.dump(options, out_file, indent='\t')
	print("done!")


if __name__ == "__main__":
	ballotbox_options()
