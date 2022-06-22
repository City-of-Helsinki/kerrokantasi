
import os

from django.conf import settings
from django.core.management import call_command


def nuke(command_options):
    default_db = settings.DATABASES["default"]
    if "sqlite" in default_db["ENGINE"]:
        db_file = default_db["NAME"]
        if os.path.isfile(db_file):
            os.unlink(db_file)
    else:
        raise NotImplementedError("Not implemented -- dunno how to nuke %s" % default_db)
    call_command("migrate", **command_options.copy())
