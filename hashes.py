import xxhash
import os
import sys

# CONSTANTS
# ---------
dl_path = '/mnt/download'
# note: symlinks not followed by default; presumably, you've intentionally
# "duplicated" the content if you've made a link to it.
# To change, set followlinks=True on os.walk.
dl_dir = os.walk(dl_path)
piece_size = 524288
# note: file count analyzed is capped for demo purposes
count_limit = 10000

if not os.path.exists(dl_path):
    print("The directory you specified doesn't exist.")
    print("Please change the value of dl_path on line 7 of the script.")
    sys.exit(1)

# MAIN
# ----
early_match = {}
full_match = {}

def build_hash(path, filesize=-1, piece_size=piece_size, start_piece=0, end_piece=-1):
    # TODO: start_piece not yet implemented
    ihash = xxhash.xxh64()
    ihandle = open(path, 'rb')

    if filesize == -1:
        # Caller failed to provide filesize, figuring it out ourselves...
        # (we trust caller-provided filesizes to size extraneous stat calls)
        filesize = os.path.getsize(path)

    #
    # figure out the largest chunk we want and allow python to control the
    # mechanics of reading up to that size.
    #
    # in a full implementation, we'd be comparing piecewise for greater
    # efficiency.
    #
    if filesize <= piece_size or end_piece == -1:
        imax = filesize
    else:
        imax = piece_size*end_piece

    ihash.update(ihandle.read(imax))
    return ihash.hexdigest()

count = 0
die_flag = False

# PRE-HASH
# --------
# Hash the first piece of each file; only do a full comparison if the first
# chunks match.
#
# If the entire file is smaller than the initial piece size, just short-circuit
# it to the full comparison lot directly.
#
for root, dirs, files in dl_dir:
    for file in files:
        item_path = os.path.join(root, file)
        isize = os.path.getsize(item_path)
        if isize <= piece_size:
            target_dict = early_match
        else:
            target_dict = full_match

        # print(f"Built path {item_path}.")
        # print ("beginning prehash... ")
        prehash = build_hash(item_path, filesize=isize, end_piece=1)
        if prehash not in target_dict:
            target_dict[prehash] = []
        target_dict[prehash].append(item_path)
        count += 1
        print(f"\rprehashing: {count} / {count_limit}", end="")
        if count > count_limit:
            die_flag = True
            break
    if die_flag:
        break
print(f" / prehashed: {count}")

# FULL-HASH
# ---------
# Hash the entire file if the first chunks are identical.
#
# list comprehensions are usually faster, so in a non-demo, we'd probably use
# these in more places.
evs = [ev for ek, ev in early_match.items() if len(ev) > 1]
evs_len = len(evs)
count = 0
for ev in evs:
    count += 1
    print(f"\rfullhashing: {count} / {evs_len}", end="")
    for e_match in ev:
        fhash = build_hash(e_match)
        if fhash not in full_match:
            full_match[fhash] = []
        full_match[fhash].append(e_match)
print(f" / fullhashed: {count}")

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
        print(f"Matching xxhash64 {dupe_k} = {','.join(dupes)}")

print(f"Done. Detected {dupe_counter} objects with {dupe_total} duplicates.")
