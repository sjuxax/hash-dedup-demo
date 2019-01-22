# Hash Dedup Demo

Quick duplicate finder. Three layers:

* "quickstat", which assumes files with the same mtime and size are the same,
  and subtracts them from the eligible hasing set; 
* pre-hash phase, where the first chunk of each file in the tree is hashed;
* full-hash phase, where files that match the first chunk are hashed in full.

To be honest the most interesting thing is `--qstat-verify`, which examines
the success rate of the quickstat grouping. It's not very good. Here's an
example summary over 250,000 in my home directory:

```
Done.
/// qstat verify on ///
qstat all:      64973
qstat ok:       44425
qstat bad:      20439
error rate:     31.46%
```

In scanning my home directory, this script found 64k files that shared an
mtime and a filesize. Of those files, 31% were not actually duplicates.

# Usage

```
usage: hashes.py [-h] [--qstat-verify] [--dump-bad-qlists] [--limit LIMIT]
                 path

positional arguments:
  path               the path to search for duplicates.

optional arguments:
  -h, --help         show this help message and exit
  --qstat-verify     run hash confirms over qstats
  --dump-bad-qlists  output bad qlist content
  --limit LIMIT      stop processing after limit files
```
