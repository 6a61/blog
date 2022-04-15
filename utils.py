import os

_metadata_cache: dict = {}

def get_metadata(path: str) -> None | dict:
	if not os.path.isfile(path):
		print("WARN: Unable to find file at " + path)
		return None


	# Check if we already have the metadata in cache or initialize with None

	if path in _metadata_cache:
		return _metadata_cache[path]
	else:
		_metadata_cache[path] = None


	# Check that the first line is a YAML block delimiter

	file = open(path)

	line = file.readline()

	if not "---" in line:
		file.close()
		return None
	

	# Scan metadata

	metadata = {}

	parsing_blogpy = False
	found_closing_line = False

	for line in file:
		if line.count(" ", 0, 1) == 0:
			if "title" == line.split(":")[0]:
				metadata["title"] = line.split(":")[1].strip().strip("\"")
				continue

			if "blog.py:" == line.rstrip():
				parsing_blogpy = True
				metadata["blog.py"] = {}
				continue

			if ("---" in line) or ("..." in line):
				found_closing_line = True
				break

		if parsing_blogpy:
			if line.count(" ", 0, 3) != 2:
				parsing_blogpy = False
				continue

			key, value = line.split(":")
			key = key.strip()
			value = value.strip()

			if key in ("public", "index"):
				metadata["blog.py"][key] = (value == "true")
			elif key in ("date"):
				metadata["blog.py"][key] = int(value)
			else:
				metadata["blog.py"][key] = value

	
	file.close()

	if not found_closing_line:
		print("WARN: Malformed metadata in file " + path)
		return None

	_metadata_cache[path] = metadata

	return metadata

def scan_directory(path, callback, recurse=False) -> list:
	try:
		dir = os.scandir(os.path.abspath(path))
		entries = []

		for entry in dir:
			if entry.is_file():
				if callback(entry):
					entries.append(entry.path)
			elif entry.is_dir() and recurse:
				sub_entries = scan_directory(entry.path, callback, recurse)

				if len(sub_entries) != 0:
					entries += sub_entries
		
		dir.close()

		return entries
	except (OSError, PermissionError) as e:
		print("WARN: Unable to access file system on " + path + ". " + e.strerror + ".")
	except BaseException as e:
		print("INFO: Unknown error while trying to access " + path + ".")
		print("      Exception: ", end='')
		print(e)