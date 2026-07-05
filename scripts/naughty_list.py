import json

import requests
import common

from scripts import common


def naughty_list():
	repo_root = common.get_repo_root()
	constants_file = repo_root / "constants.jsonc"
	constants = common.jsonc_at_home(common.read_file(constants_file))

	submissions_comments = dict()
	with open(common.get_repo_root() / "platform.ignore", 'r', encoding="utf8") as ignores_file:
		lines = ignores_file.readlines()
		for i in range(0, len(lines)):
			line = lines[i].replace("\n", "")
			if line and not lines[i].startswith("#"):
				for j in reversed(range(0, i)):
					if lines[j].startswith("#"):
						comment = lines[j].replace("\n", "").replace("# ", "")
						submissions_comments[line] = comment
						break
	genre_slug = constants["genre"]
	event_slug = constants["event"]
	submissions = dict()
	users = dict()
	submissions_url = f"https://api.modgarden.net/v2/events/{genre_slug}/{event_slug}/submissions"
	print(submissions_url)
	for submission in json.loads(requests.get(submissions_url).text):
		if submission["project"]["metadata"]["type"] != "mod":
			continue
		if submission["project"]["metadata"]["mod_id"] not in submissions_comments:
			continue
		submissions[submission["project"]["metadata"]["mod_id"]] = submission
		for user_id in submission["project"]["team"].keys():
			if user_id not in users:
				user_url = f'https://api.modgarden.net/v2/users/{user_id}'
				print(user_url)
				users[user_id] = json.loads(requests.get(user_url).text)

	print(f"Naughty list for {event_slug}:")
	for mod_id in sorted(submissions.keys()):
		submission = submissions[mod_id]
		# oh god ↓
		print(f"- **{submission["project"]["metadata"]["mod_id"]}** by {",".join([(f"<@{users[x]["integrations"]["discord"]["user_id"]}>" if "discord" in users[x]["integrations"] and "user_id" in users[x]["integrations"]["discord"] else users[x]["username"]) for x in submission["project"]["team"].keys() if users[x]["discord_id"]])} - `{submissions_comments[mod_id]}`")


if __name__ == "__main__":
	naughty_list()
