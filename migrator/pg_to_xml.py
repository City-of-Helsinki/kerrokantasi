import json

import psycopg2
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="dbname=kerrokantasi_old user=postgres")
    ap.add_argument("--xml-file", default="kerrokantasi.xml")
    ap.add_argument("--geometry-json-file", default="kerrokantasi.geometries.json")
    args = ap.parse_args()
    conn = psycopg2.connect(args.dsn)
    cur = conn.cursor()
    cur.execute("SET CLIENT_ENCODING TO 'utf8';")
    dump_xml(conn, args.xml_file)
    dump_geojson(conn, args.geometry_json_file)


def dump_xml(conn, xml_file):
    cur = conn.cursor()
    with open(xml_file, "w", encoding="utf8") as outf:
        cur.execute("SELECT database_to_xml(false, false, '');")
        row = cur.fetchone()
        outf.write(row[0])
        outf.flush()
        print("Wrote %d bytes to %s" % (outf.tell(), outf.name))


def dump_geojson(conn, geometry_json_file):
    cur = conn.cursor()
    with open(geometry_json_file, "w", encoding="utf8") as outf:
        cur.execute("SELECT id, ST_AsGeoJSON(_area, 15, 1) FROM hearing;")
        hearing_geometries = {row[0]: json.loads(row[1]) for row in cur}
        geometries = {
            "hearing": hearing_geometries
        }
        json.dump(geometries, outf, ensure_ascii=False, indent=1, sort_keys=True)
        outf.flush()
        print("Wrote %d bytes to %s" % (outf.tell(), outf.name))


if __name__ == '__main__':
    main()
