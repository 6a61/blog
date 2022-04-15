#!/usr/bin/env python

################################################################################
# blog.py
#
# CHANGELOG:
#   2022-04-13
#     - Improved command line parsing to accept pandoc options directly.
#     - Move metadata parsing function into utils.py
#     - Add index metadata parameter that, if enabled, appends at the end of the
#       file a list of entries that are public and have a date set.
#     - Move scan_directory function into utils.py
################################################################################

import argparse
import io
import os
import shutil
import subprocess
import sys
import time
import utils

if __name__ != "__main__":
	print("Module \"" + __name__ + "\" should not be imported.")
	sys.exit()

# Parse command line arguments

args = " ".join(sys.argv).split(" -- ")
pandoc_args = list()

if len(args) == 2:
	pandoc_args = args[1].split()
	args = args[0].split()
	args = args[1:len(args)]
else:
	args = args[0].split()

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', metavar='dir', type=str, required=True,
	help='input directory')
parser.add_argument('-o', '--output', metavar='dir', type=str, required=True,
	help='output directory')
parser.add_argument('-r', '--recursive', action='store_true', required=False,
	help='recurse')

parser.usage = sys.argv[0] + " -i dir -o dir [options] [-- <pandoc options>]"

if len(sys.argv) == 1:
	parser.print_help()
	sys.exit()

args = parser.parse_args(args)


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
	
	metadata = utils.get_metadata(entry.path)

	if metadata and ("blog.py" in metadata) and ("public" in metadata["blog.py"]):
		return metadata["blog.py"]["public"]

	return False

input_files = utils.scan_directory(args.input, _is_markdown_and_public, args.recursive)


# Create directories in output path

for file in input_files:
	file = file.replace(os.path.abspath(args.input), os.path.abspath(args.output))

	os.makedirs(os.path.dirname(file), exist_ok=True)


# Process input files with pandoc

for file in input_files:
	print("INFO: Processing " + file + ".")
	metadata = utils.get_metadata(file)

	output_file = file.replace(os.path.abspath(args.input), os.path.abspath(args.output))
	output_file, _ = os.path.splitext(output_file)
	output_file += ".html"

	pandoc = [
		"pandoc",
		file,
		"--output=" + output_file,
		"--from=markdown",
		"--standalone",
		"--table-of-contents",
	]

	for arg in pandoc_args:
		pandoc.append(arg)

	if metadata and ("blog.py" in metadata):
		if "date" in metadata["blog.py"]:
			date = time.strftime("%Y-%m-%d", time.localtime(metadata["blog.py"]["date"]))
			pandoc.append("--var=date:" + date)

		if ("index" in metadata["blog.py"]) and metadata["blog.py"]["index"]:
			sorted_metadata = []

			for f in input_files:
				m = utils.get_metadata(f)

				if (not "date" in m["blog.py"]) or (not "title" in m):
					continue

				sorted_metadata.append((f, m))


			def _sort_metadata(item):
				return item[1]["blog.py"]["date"]

			sorted_metadata.sort(key=_sort_metadata, reverse=True)

			index_path = shutil.copy(file, ".tmp_index.md")
			index = open(index_path, "a")
			index.write("\n\n")

			for (path, metadata) in sorted_metadata:
				formatted_date = time.strftime("%Y-%m-%d", time.localtime(metadata["blog.py"]["date"]))
				title = metadata["title"]
				url = path.replace(os.path.abspath(args.input), "")
				url, _ = os.path.splitext(url)
				url += ".html"
				url = url.replace(os.path.sep, "/")
				url = url[1:len(url)]
				
				index.write("- " + formatted_date + ": [" + title + "](" + url + ")\n")

			index.close()
			pandoc[1] = pandoc[1].replace(file, index_path)

	subprocess.run(pandoc)

	if (pandoc[1] == ".tmp_index.md"):
		os.remove(".tmp_index.md")
