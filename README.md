# blog

A static web page generator written in Python that uses
[Pandoc](https://pandoc.org).

## Requirements

- Pandoc
- Python

## Usage

```shell
usage: ./blog.py [options] [pandoc options] -i <input directory> -o <output directory>

options:
  -h, --help            show this help message and exit
  -i <input directory>, --input <input directory>
                        input directory
  -o <output directory>, --output <output directory>
                        output directory
  -r, --recursive       recurse
  -d "format", --date "format"
                        date format (ex. "%Y-%m-%d")

Any option that's not on the list will be passed directly to pandoc
```

To see a preview before uploading the files I like doing

```shell
$ python -m http.server -d <output directory>
```
