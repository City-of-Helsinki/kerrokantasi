# -*- coding: utf-8 -*-
import argparse
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
import logging

log = logging.getLogger(__name__)


def _add_to_target(target_map, object, key):
    target = None
    for id_key, ex_target in target_map.items():
        id = object.get(id_key)
        if id:
            target = ex_target[id]
            break
    if not target:
        #print("No %s target found for %r" % (key, object))
        return False
    target.setdefault(key, []).append(object)
    return target


def _process_hearings_tree(tables):
    hearings = {hearing["id"]: hearing for hearing in tables.pop("hearing")}
    alternatives = {alternative["id"]: alternative for alternative in tables.pop("alternative")}
    sections = {section["id"]: section for section in tables.pop("section")}
    comments = {comment["id"]: comment for comment in tables.pop("comment")}
    images = {image["id"]: image for image in tables.pop("image")}
    log.info(
        "Found %d hearings, %d alternatives, %d sections, %d comments and %d images",
        len(hearings),
        len(alternatives),
        len(sections),
        len(comments),
        len(images),
    )

    likes = defaultdict(list)
    for like in tables.pop("like"):
        likes[like["comment_id"]].append(like)

    map = {
        "hearing_id": hearings,
        "alternative_id": alternatives,
        "comment_id": comments,
        "section_id": sections,
    }
    for comment in comments.values():
        comment["likes"] = likes.pop(comment["id"], [])
        _add_to_target(map, comment, "comments")

    for image in images.values():
        _add_to_target(map, image, "images")

    for tab in map.values():
        for ent in tab.values():
            ent["main_image"] = images.get(ent.get("main_image_id"))

    for id, hearing in hearings.items():
        hearing["alternatives"] = [a for a in alternatives.values() if a["hearing_id"] == id]
        hearing["sections"] = [s for s in sections.values() if s["hearing_id"] == id]
    return hearings


def process_tree(xml_tree):
    tables = {
        table.tag: [{column.tag: column.text for column in row} for row in table.getchildren()]
        for table in xml_tree.find("public").getchildren()
        }
    hearings = _process_hearings_tree(tables)

    out = {
        "hearings": hearings,
        "users": {u["id"]: u for u in tables.pop("user")}
    }
    return out


def main():
    log_levels = {n.lower(): l for (n, l) in logging._nameToLevel.items()}
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", default="kerrokantasi.xml")
    ap.add_argument("--json", default="kerrokantasi.json")
    ap.add_argument("--log-level", default="info", choices=log_levels)
    args = ap.parse_args()
    logging.basicConfig(level=log_levels[args.log_level])

    tree = ET.parse(args.xml)
    tree = process_tree(tree)
    with open(args.json, "w", encoding="utf8") as outf:
        json.dump(tree, outf, ensure_ascii=False, indent=1, sort_keys=True)
        outf.flush()
        log.info("Wrote %d bytes to %s", outf.tell(), outf.name)


if __name__ == '__main__':
    main()
