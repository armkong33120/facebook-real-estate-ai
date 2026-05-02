#!/usr/bin/env python3
import os
import sys

def is_image(fname):
    return fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic'))

def main():
    base_dir = os.path.expanduser('~/Desktop/Facebook_Property_Data')
    if not os.path.isdir(base_dir):
        print(f'Base dir not found: {base_dir}')
        sys.exit(1)

    one_img_ids = set()

    # Walk provinces -> districts -> property_id
    for province in os.listdir(base_dir):
        ppath = os.path.join(base_dir, province)
        if not os.path.isdir(ppath):
            continue
        for district in os.listdir(ppath):
            dpath = os.path.join(ppath, district)
            if not os.path.isdir(dpath):
                continue
            for prop in os.listdir(dpath):
                proppath = os.path.join(dpath, prop)
                if not os.path.isdir(proppath):
                    continue
                try:
                    files = [f for f in os.listdir(proppath) if not f.startswith('.')]
                except Exception:
                    files = []
                images = [f for f in files if is_image(f) and not f.lower().startswith('temp')]
                if len(images) == 1:
                    one_img_ids.add(prop)

    print(f'Found {len(one_img_ids)} property dirs with exactly 1 image')

    uat_file = os.path.join(os.path.dirname(__file__), 'uat_links.txt')
    if not os.path.exists(uat_file):
        print(f'uat_links.txt not found at {uat_file}')
        sys.exit(1)

    matches = []
    with open(uat_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if '|' not in line:
                continue
            id_part = line.split('|', 1)[0].strip()
            if id_part in one_img_ids:
                matches.append(line.rstrip('\n'))

    out_file = os.path.join(os.path.dirname(__file__), 'uat_link.txt')
    with open(out_file, 'w', encoding='utf-8') as out:
        for l in matches:
            out.write(l + '\n')

    print(f'Wrote {len(matches)} links to {out_file}')

    matched_ids = set(m.split('|',1)[0].strip() for m in matches)
    unmatched = sorted(one_img_ids - matched_ids)
    if unmatched:
        print(f'Unmatched property IDs (no link found): {len(unmatched)}')
        for pid in unmatched[:20]:
            print(pid)

if __name__ == '__main__':
    main()
