#!/usr/bin/env python3
import xxhash
import os
import sys
import argparse
import stat
from pprint import pprint

# CONSTANTS
# ---------
cli_parser = argparse.ArgumentParser()
cli_parser.add_argument('path', help='the path to search for duplicates.')
cli_parser.add_argument('--limit', help='stop processing after limit files',
                        type=int)
cli_parser.add_argument('--min-filesize', help='skip small files',
                        type=int, default=131072)

# cli_parser.add_argument('--prehash-blocks', type=int,
#                         help='512K units to process for the prehash')
cli_args = cli_parser.parse_args()

dl_path = cli_args.path
# note: symlinks not followed by default; presumably, you've intentionally
# "duplicated" the content if you've made a link to it.
# To change, set followlinks=True on os.walk.
dl_dir = os.walk(dl_path)
piece_size = 256*1024
count_limit = cli_args.limit

if not os.path.exists(dl_path):
    print("The directory you specified doesn't exist.")
    sys.exit(1)

# MAIN
# ----
early_match = {}
full_match = {}
# stat_idx expects stat_idx[size] = [path, path, path, ...]
stat_idx = {}
handle_pool = {}

def open_handle(path, buf_sz):
    try:
        return open(path, 'rb', buf_sz)
    except:
        print(f"\nCould not open {path}, skipping.")
        return None


def build_hash(path, piece_size=piece_size, start_piece=0, end_piece=-1,
               handle_pool={}):
    # TODO: start_piece not yet implemented
    ihash = xxhash.xxh64()
    if path in handle_pool:
        ihandle = handle_pool[path]
    else:
        ihandle = open_handle(path, piece_size)
        if not ihandle:
            print(f"\nCould not open {path}, skipping.")
            return

    # in a full implementation, we'd be comparing piecewise for greater
    # efficiency.

    if end_piece == -1:
        imax = -1
    else:
        imax = piece_size*end_piece

    try:
        ihash.update(ihandle.read1(imax))
    except PermissionError:
        # some files won't allow us to read -- just abort here
        return None
    return ihash.hexdigest()

count = 0
quickstat_count = 0
die_flag = False
irreg_count = 0

# QUICKSTAT
# --------
# stats the entire directory tree and uses the size header to determine
# if there are potential duplicates within the tree.
#
# There is a theoretical possibility of risk/damage with this, especially as it
# pertains to things like sparse files. Watch your butt. A flag to allow the
# user to distrust size headers would be a nice-to-have.
#
for root, dirs, files in dl_dir:
    for file in files:
        item_path = os.path.join(root, file)

        stat_ret = os.stat(item_path, follow_symlinks=False)
        quickstat_count += 1
        print(f"\r quickstatting: {quickstat_count} / {count_limit} ", end="",
              file=sys.stderr)

        if not stat.S_ISREG(stat_ret.st_mode):
            # skip all irregular files
            irreg_count += 1
            continue

        sz = stat_ret.st_size
        if sz < cli_args.min_filesize:
            # skip tiny files
            continue

        if sz not in stat_idx:
            stat_idx[sz] = []
        stat_idx[sz].append(item_path)
        if count_limit and quickstat_count >= count_limit:
            die_flag = True
            break
    if die_flag:
        break
print(f" / quickstatted: {quickstat_count}")

do_hash = []

for sz_key, sz_vals in stat_idx.items():
        sz_len = len(sz_vals)
        if sz_len > 1:
            [do_hash.append(p) for p in sz_vals]

do_hash_len = len(do_hash)

print(f"quickstat discovered {do_hash_len} items to hash")

# PRE-HASH
# --------
# Hash the first piece of each file; only do a full comparison if the first
# chunks match.
#
for item_path in do_hash:
    prehash = build_hash(item_path, end_piece=4)
    if prehash == None:
        # print("Aborting hash.")
        continue
    if prehash not in early_match:
        early_match[prehash] = []
    early_match[prehash].append(item_path)
    count += 1

    if not count_limit or do_hash_len < count_limit:
        cl_display = do_hash_len
    else:
        cl_display = count_limit

    print(f"\rprehashing: {count} / {cl_display}", end="", file=sys.stderr)
    if count_limit and count >= count_limit:
        die_flag = True
        break
print(f" / prehashed: {count}")

# FULL-HASH
# ---------
# Hash the entire file if the first chunks are identical.
#
evs = [ev for ek, ev in early_match.items() if len(ev) > 1]
evs_len = len(evs)
full_count = 0
for ev in evs:
    full_count += 1
    print(f"\rfullhashing: {full_count} / {evs_len}", end="", file=sys.stderr)
    for e_match in ev:
        fhash = build_hash(e_match)
        if fhash not in full_match:
            full_match[fhash] = []
        full_match[fhash].append(e_match)
print(f" / fullhashed: {full_count}")

# RESULTS
# -------
# Print out the results.
#
dupe_counter = 0
dupe_total = 0

for dupe_k, dupes in full_match.items():
    dlen = len(dupes)
    dupe_total += (dlen-1)
    if dlen > 1:
        dupe_counter += 1
        print(f"Matching xxhash64 {dupe_k}\n\t{','.join(dupes)}")

print("----- ----- ----- ----- ----- ----- ")
print(f"Done.")
print(f"Detected {do_hash_len} candidate matches from {quickstat_count} files.")
print(f"Prehashed {count} files and full-hashed {full_count} files.")
print(f"xxhash detected {dupe_counter} files with {dupe_total} duplicates.")
print(f"Total duplicates: {dupe_total}")
