import argparse
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic

from democracy.importing.json_importer import import_from_data
from democracy.management.utils import nuke


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=argparse.FileType("r", encoding="utf8"), nargs=1)
        parser.add_argument("--hearing", nargs=1)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--patch", action="store_true")
        parser.add_argument("--nuke", dest="nuke", action="store_true")

    def handle(self, input_file, **options):
        if options.pop("nuke", False):
            nuke(command_options=options)
        verbosity_to_level = {
            0: logging.WARN,
            1: logging.INFO,
            2: logging.DEBUG,
            3: logging.DEBUG,
        }
        logging.basicConfig(level=verbosity_to_level[options["verbosity"]])
        hearing = options.pop("hearing")
        if hearing:
            hearing = hearing[0]
        self.do_import(input_file[0],
                       hearing=hearing,
                       force=options.pop("force", False),
                       patch=options.pop("patch", False))

    @atomic
    def do_import(self, filename, hearing=None, force=False, patch=False):
        json_data = json.load(filename)
        if hearing:
            # picks the hearing corresponding to given slug
            try:
                hearing_data = next(value for key, value in json_data['hearings'].items() if value['slug'] == hearing)
            except StopIteration:
                raise CommandError('Hearing "%s" does not exist' % hearing)
            json_data = {'hearings': {'1': hearing_data}}
        import_from_data(json_data, force=force, patch=patch)
