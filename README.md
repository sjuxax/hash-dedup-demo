# Hash Dedup Demo

Quick duplicate finder. Three layers:

* "quickstat", which populates the list of candidate identical files by only
    considering files with non-unique sizes. A damaged filesystem could still
    break this, but good enough for now;
* pre-hash phase, where the first chunk of each file in the tree is hashed;
* full-hash phase, where files that match the first chunk are hashed in full.

```
usage: hashes.py [-h] [--limit LIMIT]
                 path

positional arguments:
  path               the path to search for duplicates.

optional arguments:
  -h, --help         show this help message and exit
  --limit LIMIT      stop processing after limit files
```
