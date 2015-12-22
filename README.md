
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
     
## Compile translation .mo files (if i18n is required)

     python manage.py i18n:compile

# Migration

1. Import the dump of a Kuulemma database into your PostgreSQL instance
   (the default expected database name is `kerrokantasi_old`).
2. Run `migrator/process_legacy_data.py -p`; if the PG database is `kerrokantasi_old`, no arguments
   should be necessary. (Otherwise, see `--help`.)  This will generate three files:
   * `kerrokantasi.xml` -- an XML dump of the original PG database
   * `kerrokantasi.geometries.json` -- a temporary JSON file of the GIS geometries in the original PG database
   * `kerrokantasi.json` -- a reformatted amalgamation of the XML and geometry files to be ingested by the
     `democracy_import_json` management command.
3. Copy the `images` directory from your Kuulemma filesystem's `kuulemma/static` directory
   to the `kerrokantasi` media directory (defaults to `kerrokantasi/var/media`).
4. Run the `democracy_import_json` management command with the path of the JSON file created in step 3.
5. Done.

# Development

## Testing

To run all tests, execute command in project root directory.

     py.test

Run test against particular issue.

    py.test -k test_7 -v

## Internationalization

Translations are maintained on [Transifex][tx].

* To pull new translations from Transifex, run `npm run i18n:pull`
* As a translation maintainer, run `npm run i18n:extract && npm run i18n:push` to push new source files.

[tx]: https://www.transifex.com/city-of-helsinki/kerrokantasi/dashboard/
