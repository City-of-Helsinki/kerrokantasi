import psycopg2
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="dbname=kerrokantasi_old user=postgres")
    ap.add_argument("--file", default="kerrokantasi.xml")
    args = ap.parse_args()

    conn = psycopg2.connect(args.dsn)
    cur = conn.cursor()
    cur.execute("SET CLIENT_ENCODING TO 'utf8';")
    cur.execute("SELECT database_to_xml(false, false, '');")
    with open(args.file, "wb") as outf:
        row = cur.fetchone()
        outf.write(row[0].encode("UTF-8"))
        outf.flush()
        print("Wrote %d bytes to %s" % (outf.tell(), outf.name))

if __name__ == '__main__':
    main()
