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

# qstat-verify format

`qstat-verify` mode has some cryptic output:

```
qlist 140407286836424 (len 2): *7f937 +
qlist 140407286836680 (len 2): *c3c9a +
qlist 140407260916808 (len 3): *f2d1a + +
qlist 140407262201480 (len 2): *bc756 +
qlist 140407262174728 (len 12): *69256 + + + + + + + + + + +
qlist 140407286066248 (len 2): *01e65 -
qlist 140407282696392 (len 2): *01e65 -
qlist 140407286097800 (len 2): *a2824 -
```

Breaking this down, it's: `'qlist' id(qlist) (length of qlist):
*hash-of-first-item[:5]` followed by either `+` (a "good qstat") if the hash
matches the preceding value, or `-` if not (a "bad qstat", which taints this
to a "bad qlist").

Invoking with `--dump-bad-qlists` will output the hashes and paths of
mismatched files.

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
