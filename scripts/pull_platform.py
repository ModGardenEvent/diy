#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import requests

import common
from assemble_packwiz import SubmissionLockfileFormat
from common import Ansi


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

	for idx, submission in enumerate(submission_data):
		if submission["project"]["metadata"]["type"] != "mod":
			submission_data.pop(idx)

	# Update the lock file
	# Read the needed files and transform the submission data into a dict where the ids are keys
	lock_data: SubmissionLockfileFormat = json.loads(common.read_file(submission_lock_file)) if submission_lock_file.exists() else {}
	submissions_by_mod_id = {s["project"]["metadata"]["mod_id"]: s for s in submission_data}

	# Remove stale data
	lock_data = {k: v for k, v in lock_data.items() if (k in submissions_by_mod_id)}

	# Loop through all submissions
	rate_limit = common.Ratelimiter(1)
	for mod_id in submissions_by_mod_id:
		submission_info = submissions_by_mod_id[mod_id]
		platform_info = dict()
		platform_info["type"] = submission_info["platform"]["type"]
		if platform_info["type"] == "modrinth":
			platform_info["version_id"] = submission_info["platform"]["version_id"]
			platform_info["project_id"] = submission_info["platform"]["project_id"]
		elif platform_info["type"] == "download_url":
			platform_info["download_url"] = submission_info["platform"]["download_url"]
		else:
			print(f"{mod_id} has an unsupported platform type '{platform['type']}'")
			continue

		lock_info = lock_data.get(mod_id)  # Might be None
		submission_hash = hashlib.sha256(json.dumps(platform_info, sort_keys=True).encode("utf-8")).digest().hex()
		# If the platform info changes we need to update the lock data
		if lock_info is None or lock_info["key"] != submission_hash:
			print(f"Updating lock data for {mod_id}")
			lock_info = {}  # Reset the lock info for this mod
			assert lock_info is not None  # mypy is quite stupid
			lock_info["key"] = submission_hash

			old_dir = os.getcwd()

			# We steal packwiz's dependency resolution by making a quick packwiz dir
			with tempfile.TemporaryDirectory() as tmpdir_name:
				tmpdir = Path(tmpdir_name)
				# Run commands in the temporary directory

				os.chdir(tmpdir)

				# This is the minimum for packwiz to consider this a pack dir
				shutil.copyfile(packwiz_pack_toml, tmpdir / "pack.toml")
				(tmpdir / "index.toml").touch()

				# Install the mod into the temporary packwiz pack
				rate_limit.limit()
				if platform_info["type"] == "modrinth":
					subprocess.run([packwiz, "modrinth", "install", "--project-id", platform_info["project_id"], "--version-id", platform_info["version_id"], "-y"])
				elif platform_info["type"] == "download_url":
					subprocess.run([packwiz, "url", "add", mod_id, platform_info["download_url"], "-y"])

				# Now lets see which files packwiz thought we should download
				files = {}
				for packwiz_meta in tmpdir.rglob("**/*.pw.toml"):
					packwiz_data = tomllib.loads(common.read_file(tmpdir / packwiz_meta))
					if "update" in packwiz_data:
						del packwiz_data["update"]
					files[str(packwiz_meta.relative_to(tmpdir)).replace("\\", "/")] = packwiz_data
				if len(files) == 0:
					print(f"{Ansi.WARN}Packwiz didn't generate any mod files for {mod_id}{Ansi.RESET}")
				lock_info["files"] = files

				os.chdir(old_dir)
		lock_data[mod_id] = lock_info

	# Write the update lock data back
	with open(submission_lock_file, "w") as f:
		f.write(json.dumps(lock_data, indent='\t', sort_keys=True))

	# Make it clear that this script didn't really do anything if event_slug or genre_slug are null
	if event_slug == None or genre_slug == None:
		sys.exit(1)


if __name__ == "__main__":
	main()
