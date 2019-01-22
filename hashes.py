#!/usr/bin/env python3
import xxhash
import os
import sys
# import pprint

# CONSTANTS
# ---------
dl_path = '/mnt/download'
# note: symlinks not followed by default; presumably, you've intentionally
# "duplicated" the content if you've made a link to it.
# To change, set followlinks=True on os.walk.
dl_dir = os.walk(dl_path)
piece_size = 524288
# note: file count analyzed is capped for demo purposes
count_limit = None

if not os.path.exists(dl_path):
    print("The directory you specified doesn't exist.")
    print("Please change the value of dl_path on line 7 of the script.")
    sys.exit(1)

# MAIN
# ----
early_match = {}
full_match = {}
# stat_idx expects stat_idx[size][mtime] = [path, path, path, ...]
stat_idx = {}

def build_hash(path, piece_size=piece_size, start_piece=0, end_piece=-1):
    # TODO: start_piece not yet implemented
    ihash = xxhash.xxh64()
    try:
        ihandle = open(path, 'rb')
    except:
        print(f"\nCould not open {path}, skipping.")
        return None

    # in a full implementation, we'd be comparing piecewise for greater
    # efficiency.

    if end_piece == -1:
        imax = -1
    else:
        imax = piece_size*end_piece

    ihash.update(ihandle.read1(imax))
    return ihash.hexdigest()

count = 0
quickstat_count = 0
die_flag = False

# QUICKSTAT
# --------
# stats the entire directory tree and considers files with identical
# mtime/filesize pairs as duplicates.
#
# This hack is well-known. For example, rsync operates in this mode by default.
# If a file has the same name, size, and mtime, its content is considered
# identical unless the --checksum/-C flag is passed. The difference is that
# rsync has an authoritative copy on the source side of the equation.
#
# We intentionally didn't implement this hack in the first pass due to the
# problem's emphasis on 100% correctness. This WILL yield false positives.
#
# qstat reports should always be verified before action is taken.
#
for root, dirs, files in dl_dir:
    for file in files:
        item_path = os.path.join(root, file)

        # use mtime and size as an approximation of sameness
        # per convention, this can be disabled with -C.
        stat_ret = os.stat(item_path, follow_symlinks=False)

        sz = stat_ret.st_size
        mtime = stat_ret.st_mtime

        if sz not in stat_idx:
            stat_idx[sz] = {}
        if mtime not in stat_idx[sz]:
            stat_idx[sz][mtime] = []
        stat_idx[sz][mtime].append(item_path)
        quickstat_count += 1
        print(f"\r quickstatting: {quickstat_count} / {count_limit} ", end="")
        if count_limit and quickstat_count >= count_limit:
            die_flag = True
            break
    if die_flag:
        break
print(f" / quickstatted: {quickstat_count}")

do_hash = []
qstat_dupes = []
qstat_dupes_counter = 0

for sz_key, mtime_vals in stat_idx.items():
    for mtime_key, path_vals in mtime_vals.items():
        pval_len = len(path_vals)
        if pval_len == 1:
            [do_hash.append(p) for p in path_vals]
        elif pval_len > 1:
            qstat_dupes.append(path_vals)
            qstat_dupes_counter += pval_len
            # print(f"sz_key: {sz_key}, mtime_key: {mtime_key}")
            # pprint.pprint(path_vals)

do_hash_len = len(do_hash)

print(f"quickstat discovered {qstat_dupes_counter} known dups")
print(f"quickstat discovered {do_hash_len} items to hash")

# PRE-HASH
# --------
# Hash the first piece of each file; only do a full comparison if the first
# chunks match.
#
for item_path in do_hash:
    prehash = build_hash(item_path, end_piece=1)
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

    print(f"\rprehashing: {count} / {cl_display}", end="")
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
    print(f"\rfullhashing: {full_count} / {evs_len}", end="")
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
for qlist in qstat_dupes:
    print(f"Matching qstats\n\t{','.join(qlist)}")

for dupe_k, dupes in full_match.items():
    dlen = len(dupes)
    dupe_total += (dlen-1)
    if dlen > 1:
        dupe_counter += 1
        print(f"Matching xxhash64 {dupe_k}\n\t{','.join(dupes)}")

print("----- ----- ----- ----- ----- ----- ")
print(f"Done.")
print(f"Detected {qstat_dupes_counter} files during quickstat dedup.")
print(f"Prehashed {count} files and full-hashed {full_count} files.")
print(f"xxhash detected {dupe_counter} files with {dupe_total} duplicates.")
print(f"Total duplicates: {dupe_total+qstat_dupes_counter}")
