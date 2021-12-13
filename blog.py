#!/usr/bin/env python

import argparse
import os
import sys
import subprocess

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input', metavar='dir', type=str, required=True,
		help='Input directory')
	parser.add_argument('-o', '--output', metavar='dir', type=str, required=True,
		help='Output directory')
	parser.add_argument('-t', '--template', metavar='file|url', type=str, required=False,
		help='Specify custom template')
	parser.add_argument('-w', '--whitelist', metavar='file', type=str, required=False,
		help='Whitelist file')
	parser.add_argument('-r', '--recursive', action='store_true', required=False,
		help='Recurse')
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

	# Parse whitelist

	whitelist = None

	if args.whitelist:
		try:
			file = open(os.fsencode(args.whitelist))

			for line in file:
				# Ignore empty lines and comments

				if len(line) == 1 or line[0] == '#':
					continue

				# Strip \n if it appears at the end

				if line[-1] == '\n':
					line = line[0:-1]

				# Windows: Replace forward slashes with backward slashes

				line = line.replace('/', os.sep)

				if not whitelist:
					whitelist = []

				whitelist.append(line)

			file.close()
		except OSError:
			print("WARN: Unable to open " + args.whitelist + ". Whitelist will be ignored.")

	# Parse input directory

	def scandir(path):
		try:
			dir = os.scandir(os.path.abspath(path))
			entries = []

			for entry in dir:
				if entry.is_file():
					# Accept only markdown files
					
					_, extension = os.path.splitext(entry.path)

					if extension != ".md":
						continue

					# Check entry against whitelist (if enabled)

					if whitelist:
						for whitelist_item in whitelist:
							if whitelist_item in entry.path:
								entries.append(entry.path)
								break
					else:
						entries.append(entry.path)
				elif entry.is_dir() and args.recursive:
					sub_entries = scandir(entry.path)

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
	
	input_files = scandir(args.input)

	# Create directories in output path

	# NOTE: Current implementation attempts to create a directory for each file,
	# even if the directory was created by a previous file.

	for file in input_files:
		file = file.replace(os.path.abspath(args.input), os.path.abspath(args.output))
		os.makedirs(os.path.dirname(file), exist_ok=True)
	
	# Process input files with pandoc

	for file in input_files:
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
		]

		if args.css:
			pandoc.append("--css=" + args.css)
		
		if args.template:
			pandoc.append("--template=" + args.template)
		
		subprocess.run(pandoc)