
# Requirements

 - Python 3.4
 - Django 1.8.5
 - django-modeltranslation (http://django-modeltranslation.readthedocs.org)
 - Django REST framework (http://www.django-rest-framework.org/)
 - munigeo (https://github.com/City-of-Helsinki/munigeo)
 - django-reversion (http://django-reversion.readthedocs.org)

# Install

## Prepare virtualenv

     virtualenv -p /usr/bin/python3 ~/.virtualenvs/
     workon kerrokantasi

## Install required packages

Install all required packages with pip command:

     pip install -r requirements.txt

# Testing

Run all tests. Execute command in project root directory.

     py.test

Run test against particular issue.

    py.test -k test_7 -v

# Migration

1. Import the dump of a Kuulemma database into your PostgreSQL instance
   (the default expected database name is `kerrokantasi_old`).
2. Run `migrator/pg_to_xml.py`; if the PG database is `kerrokantasi_old`, no arguments
   should be necessary. (Otherwise, see `--help`.)
3. Run `migrator/xml_to_json.py`; no arguments should be necessary.
4. Copy the `images` directory from your Kuulemma filesystem's `kuulemma/static` directory
   to the `kerrokantasi` media directory (defaults to `kerrokantasi/var/media`).
5. Run the `kk_import_json` management command with the path of the JSON file created in step 3.
6. Done.
