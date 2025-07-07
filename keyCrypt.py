#!/usr/bin/env python3

import os
import subprocess
import sys

from cryptography.fernet import Fernet


def throw_error(error, value=None):
	errors = {
		"DK": f"{value} Duplicate Key" if value else "Duplicate Key",
		"EI": "Empty Input",
		"IF": "Invalid Format",
		"NF": f"{value} Not Found" if value else "Not Found",
	}

	print(f"\033[91mERROR\033[0m {errors[error]}")
	sys.exit(1)


def get_validate_input():
	entry = input("-> ").strip()
	if not entry:
		throw_error("EI")

	if ":" not in entry or not all(part.strip() for part in entry.split(":", 1)):
		throw_error("IF")

	return entry


class KeyCrypt:
	def __init__(self, _file, _param):
		self.file = _file
		self.param = _param
		self.old_key, self.data = self.read_data()

	############
	# COMMANDS #
	############

	def exe(self):
		decrypted = self.decrypt()

		match = decrypted.get(self.param)
		if not match:
			throw_error("NF", self.param)

		subprocess.run("clip", input=str(match), text=True, check=True)

		self.encrypt(decrypted)
		return

	def list(self):
		decrypted = self.decrypt()
		for key in decrypted:
			print(key)

	def create(self):
		entry = get_validate_input()

		key, value = entry.split(":")
		decrypted = self.decrypt()

		if decrypted.get(key):
			throw_error("DK", key)

		decrypted[key] = value.strip()

		self.encrypt(decrypted)

	def update(self):
		entry = get_validate_input()

		key, value = entry.split(":")
		decrypted = self.decrypt()

		if not decrypted.get(key):
			throw_error("NF", key)

		# Update old key with new value
		decrypted[key] = value.strip()

		self.encrypt(decrypted)

	def delete(self):
		entry = input("-> ").strip()
		if not entry:
			throw_error("EI")

		decrypted = self.decrypt()

		if not decrypted.get(entry):
			throw_error("NF", entry)

		del decrypted[entry]

		self.encrypt(decrypted)

	def wipe(self):
		ans = input("y/n?")
		if ans != "y":
			print("n")
			sys.exit(1)

		with open(self.file, "w"):
			pass

	####################
	# BACKGROUND TASKS #
	####################

	def read_data(self):
		with open(self.file, "rb") as read_file:
			lines = read_file.readlines()

			if lines:
				old_key = lines[0].strip()
				return old_key, lines[1:]

		# In case the file is empty, generate new key and save it
		old_key = Fernet.generate_key()
		with open(self.file, "ab") as write_file:
			write_file.write(old_key + b"\n")

		return old_key, []

	def decrypt(self):
		decrypted = [Fernet(self.old_key).decrypt(line.strip()) for line in self.data]

		hashmap = {}
		for line in decrypted:
			key, value = line.decode().split(":")
			hashmap[key] = value.strip()

		return hashmap

	def encrypt(self, data):
		new_key = Fernet.generate_key()
		lines = [Fernet(new_key).encrypt(f"{key}:{value}".encode()) + b"\n" for key, value in data.items()]
		lines.insert(0, new_key + b"\n")

		with open(self.file, "wb") as txtfile:
			txtfile.writelines(lines)


file = None
for item in os.listdir():
	if os.path.isfile(item) and item not in ["keyCrypt.py", "README.txt", "requirements.txt"]:
		file = item
		break

if not file:
	throw_error("NF", "File")

param = sys.argv[1] if len(sys.argv) > 1 else None

if not param:
	throw_error("NF", "Param")

script = KeyCrypt(file, param)

# Create a dict of methods where the console command must correspond to an actual method of script obj
commands = {command: getattr(script, command) for command in ["list", "create", "update", "delete", "wipe"]}

# Dynamically call the match method from the dict above, fallback to exe()
commands.get(param, script.exe)()
