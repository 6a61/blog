#!/usr/bin/env python

################################################################################
# blog.py
#
# TODO:
#   - Make title-prefix a command line argument.
#   - Add "index (blog?)" option to make an aggregator of entries (which ones?).
################################################################################

import argparse
import os
import sys
import subprocess
import io

def parse_metadata(path: str) -> None | dict:
	try:
		f = open(path)

		# Check that file begins with metadata

		line = f.readline()

		if not "---" in line:
			f.close()
			return None

		# Parse metadata

		parsing = False

		metadata = {
			"public": False,
			"date": None,
		}

		for line in f:
			if line.rstrip() == "blog.py:":
				parsing = True
				continue

			if parsing:
				# No more than two spaces for each item under blog.py
				if line.count(" ", 0, 3) > 2:
					print("WARN: Malformed metadata in file " + path + ".")
					return None

				if "public:" in line:
					metadata["public"] = "true" in line
				elif "date:" in line:
					metadata["date"] = int(line.split(":")[1].strip())
				elif not "---" in line:
					print("WARN: Unknown metadata parameter " + line.split(":")[0].strip() + " in file " + path + ".")
			
			if "---" in line:
				parsing = False
				break
		
		f.close()

		if parsing:
			print("WARN: Cannot find end of metadata.")
			return None
		
		return metadata

	except OSError:
		print("WARN: Unable to open " + path + ".")
		return None

def scan_directory(path, callback) -> list:
	try:
		dir = os.scandir(os.path.abspath(path))
		entries = []

		for entry in dir:
			if entry.is_file():
				if callback(entry):
					entries.append(entry.path)
			elif entry.is_dir() and args.recursive:
				sub_entries = scan_directory(entry.path, callback)

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

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', metavar='dir', type=str, required=True,
		help='input directory')
	parser.add_argument('-o', '--output', metavar='dir', type=str, required=True,
		help='output directory')
	parser.add_argument('-t', '--template', metavar='file|url', type=str, required=False,
		help='specify custom template')
	parser.add_argument('-r', '--recursive', action='store_true', required=False,
		help='recurse')
	parser.add_argument('--css', metavar='url', type=str, required=False,
		help='CSS')

	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit()

	args = parser.parse_args()

	# Check directories exists

	if not os.path.exists(os.path.abspath(args.input)):
		print("ERROR: Input directory does not exists")
		sys.exit()

	# Create output directory if it does not exist

	os.makedirs(os.path.abspath(args.output), exist_ok=True)

	# Parse input directory

	def _is_markdown_and_public(entry):
		# Check that files have the .md extension and are public

		_, extension = os.path.splitext(entry.path)

		if extension.lower() != ".md":
			return False
		
		metadata = parse_metadata(entry.path)

		if metadata and metadata["public"]:
			return True

		return False

	input_files = scan_directory(args.input, _is_markdown_and_public)

	# Create directories in output path

	for file in input_files:
		file = file.replace(os.path.abspath(args.input), os.path.abspath(args.output))

		os.makedirs(os.path.dirname(file), exist_ok=True)
	
	# Process input files with pandoc

	for file in input_files:
		print("INFO: Processing " + file + ".")

		output_file = file.replace(os.path.abspath(args.input), os.path.abspath(args.output))
		output_file, _ = os.path.splitext(output_file)
		output_file += ".html"

		pandoc = [
			"pandoc",
			file,
			"--output=" + output_file,
			"--from=markdown",
			"--katex",
			"--standalone",
			"--table-of-contents",
			"--title-prefix=" + "blog.py",
		]

		if args.css:
			pandoc.append("--css=" + args.css)
		
		if args.template:
			pandoc.append("--template=" + args.template)
		
		subprocess.run(pandoc)
