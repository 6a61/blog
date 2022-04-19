#!/usr/bin/env python

################################################################################
# blog.py
#
# CHANGELOG:
#   2022-04-15
#     - Improve command line parsing behaviour
#     - Add date command line argument
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

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', metavar='dir', type=str, required=True,
	help='input directory')
parser.add_argument('-o', '--output', metavar='dir', type=str, required=True,
	help='output directory')
parser.add_argument('-r', '--recursive', action='store_true', required=False,
	help='recurse')
parser.add_argument('-d', '--date', metavar='\"format\"', type=ascii, required=False,
	help='date format (ex. \"%%Y-%%m-%%d\")', default="%Y-%m-%d")

parser.usage = sys.argv[0] + " -i dir -o dir [options] [pandoc options]"
parser.epilog = "Any option that's not on the list will be passed directly to pandoc"

if len(sys.argv) == 1:
	parser.print_help()
	sys.exit()

args, pandoc_args = parser.parse_known_args(sys.argv)

# Remove first argument which should be the program's name
pandoc_args = pandoc_args[1:len(pandoc_args)]

# Strip apostrophes, which make date display dirty
args.date = args.date.strip("'") 


# Check if input directory exists

if not os.path.exists(os.path.abspath(args.input)):
	print("ERROR: Input directory does not exists")
	sys.exit()


# Create output directory if it does not exist

os.makedirs(os.path.abspath(args.output), exist_ok=True)


# Parse input directory for valid files (ie. files that have the .md extension
# and have the blog.py public parameter set to true)

def _is_markdown_and_public(entry):
	_, extension = os.path.splitext(entry.path)

	if extension.lower() != ".md":
		return False
	
	metadata = utils.get_metadata(entry.path)

	if (not metadata) or (not "blog.py" in metadata) or (not "public" in metadata["blog.py"]):
		return False
	
	return metadata["blog.py"]["public"]

input_files = utils.scan_directory(args.input, _is_markdown_and_public, args.recursive)


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
		"--standalone",
		"--table-of-contents",
	]

	pandoc += pandoc_args

	metadata = utils.get_metadata(file)

	if "date" in metadata["blog.py"]:
		date = time.localtime(metadata["blog.py"]["date"])
		date = time.strftime(args.date, date)
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

		metafile = open(".metadata.yaml", "w")
		metafile.write("index:\n")

		for (path, metadata) in sorted_metadata:
			proc = subprocess.Popen(["pandoc"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			title = proc.communicate(metadata["title"].encode())[0].decode()
			title = title.strip().removeprefix("<p>").removesuffix("</p>")

			metafile.write("  - title: " + title + "\n")

			formatted_date = time.localtime(metadata["blog.py"]["date"])
			formatted_date = time.strftime(args.date, formatted_date)

			metafile.write("    date: " + formatted_date + "\n")

			url = path.replace(os.path.abspath(args.input), "")
			url, _ = os.path.splitext(url)
			url += ".html"
			url = url.replace(os.path.sep, "/")
			url = url[1:len(url)]

			metafile.write("    url: " + url + "\n")

		metafile.close()
		pandoc.append("--metadata-file=.metadata.yaml")

	# Finally, call pandoc
	subprocess.run(pandoc)

	# Cleanup
	if os.path.exists(".metadata.yaml"):
		os.remove(".metadata.yaml")