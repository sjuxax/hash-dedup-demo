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
count_limit = None

if not os.path.exists(dl_path):
    print("The directory you specified doesn't exist.")
    print("Please change the value of dl_path on line 7 of the script.")
    sys.exit(1)

# MAIN
# ----
early_match = {}
full_match = {}

def build_hash(path, piece_size=piece_size, start_piece=0, end_piece=-1):
    # TODO: start_piece not yet implemented
    ihash = xxhash.xxh64()
    try:
        ihandle = open(path, 'rb')
    except:
        print(f"Could not open {path}, skipping.")
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
die_flag = False

# PRE-HASH
# --------
# Hash the first piece of each file; only do a full comparison if the first
# chunks match.
#
for root, dirs, files in dl_dir:
    for file in files:
        item_path = os.path.join(root, file)

        target_dict = early_match
        # print(f"Built path {item_path}.")
        # print ("beginning prehash... ")
        prehash = build_hash(item_path, end_piece=1)
        if prehash == None:
            # print("Aborting hash.")
            continue
        if prehash not in target_dict:
            target_dict[prehash] = []
        target_dict[prehash].append(item_path)
        count += 1

        if not count_limit:
            cl_display = "???"
        else:
            cl_display = count_limit

        print(f"\rprehashing: {count} / {cl_display}", end="")
        if count_limit and count > count_limit:
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
for dupe_k, dupes in full_match.items():
    dlen = len(dupes)
    dupe_total += (dlen-1)
    if dlen > 1:
        dupe_counter += 1
        print(f"Matching xxhash64 {dupe_k} = {','.join(dupes)}")

print("-----")
print(f"Done. Detected {dupe_counter} objects with {dupe_total} duplicates.")
print(f"Prehashed {count} and full-hashed {full_count}")
