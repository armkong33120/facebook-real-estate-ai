#!/usr/bin/env python3
import os
import sys

def is_image(fname):
    f = fname.lower()
    return f.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic'))

def main():
    base_dir = os.path.expanduser('~/Desktop/Facebook_Property_Data')
    if not os.path.isdir(base_dir):
        print(f"Base dir not found: {base_dir}")
        sys.exit(1)

    prop_infos = []  # list of (prop_id, path, image_count)

    for root, dirs, files in os.walk(base_dir):
        # ignore system files
        files = [f for f in files if not f.startswith('.')]
        image_files = [f for f in files if is_image(f) and not f.lower().startswith('temp')]
        txt_files = [f for f in files if f.lower().endswith('.txt')]
        if image_files or txt_files:
            prop_id = os.path.basename(root)
            # skip the top-level base dir
            if os.path.abspath(root) == os.path.abspath(base_dir):
                continue
            img_count = len(image_files)
            prop_infos.append((prop_id, root, img_count))

    prop_infos.sort(key=lambda x: x[0])

    # read processed count from processed_ids.txt if available
    processed_count = 0
    proc_file = os.path.join(os.path.dirname(__file__), 'processed_ids.txt')
    if os.path.exists(proc_file):
        try:
            with open(proc_file, 'r', encoding='utf-8', errors='ignore') as f:
                processed_count = sum(1 for l in f if l.strip())
        except Exception:
            processed_count = 0

    bad = [(pid, path, cnt) for (pid, path, cnt) in prop_infos if cnt < 5]

    print(f"Base dir: {base_dir}")
    print(f"Property dirs found (with text/images): {len(prop_infos)}")
    print(f"Processed IDs (lines in processed_ids.txt): {processed_count}")
    print()
    print(f"Properties with <5 images: {len(bad)}")
    if processed_count:
        pct = len(bad) * 100.0 / processed_count
        print(f"Percent of processed runs with <5 images: {pct:.2f}% ({len(bad)}/{processed_count})")
    else:
        denom = len(prop_infos) if prop_infos else 1
        pct = len(bad) * 100.0 / denom
        print(f"Percent (relative to found dirs): {pct:.2f}% ({len(bad)}/{denom})")

    print('\nList of property IDs with image counts (<5):')
    for pid, path, cnt in bad:
        print(f"{pid} | images={cnt} | path={path}")

if __name__ == '__main__':
    main()
