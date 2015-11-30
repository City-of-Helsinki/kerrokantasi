import argparse
import json
import logging

from django.core.management.base import BaseCommand
from django.db.transaction import atomic

from kk.importing.json_importer import import_from_data
from kk.management.commands.utils import nuke


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=argparse.FileType("r", encoding="utf8"), nargs=1)
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
        self.do_import(input_file[0])

    @atomic
    def do_import(self, filename):
        json_data = json.load(filename)
        import_from_data(json_data)
