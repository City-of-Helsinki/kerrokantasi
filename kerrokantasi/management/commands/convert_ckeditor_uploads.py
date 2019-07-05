
import os
import re
from collections import namedtuple

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from democracy.models import Section, SectionFile, SectionImage


class UploadedFile(namedtuple('UploadedFile', 'url, year, month, day, filename')):
    @property
    def path(self):
        return os.path.join(settings.MEDIA_ROOT, 'uploads', self.year, self.month, self.day, self.filename)


class Command(BaseCommand):
    """ Look at all section content trying to identify media files uploaded via ckeditor through the admin page.
    Move all found files to the sendfile protected storage, create SectionFile objects for them and replace the
    links in the section content with new download url.

    If the item is inside an image tag (not a link), convert the item to section image instead and move to image storage.
    """
    CKEDITOR_UPLOAD_REGEX = r'(?P<tag>(<img.*?src="|<a.*?href="))[^"]*?({}/media/uploads/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<filename>[\w.\-]+))"'

    def add_arguments(self, parser):
        parser.add_argument("--dry", action="store_true", help="Execute dry run")
        parser.add_argument("--domain", default="https://api.hel.fi/kerrokantasi", help="Root URL of the service")

    def handle(self, **options):
        self.dry_run = options.pop('dry', False)
        self.domain = options.pop('domain')
        self.regex = re.compile(self.CKEDITOR_UPLOAD_REGEX.format(self.domain))
        all_sections = Section.objects.all()
        section_count = all_sections.count()
        counter = 0
        moved_files = {}  # mapping of parsed urls to sectionfiles
        for section in all_sections:
            counter += 1
            self.stdout.write('Section [{}/{}]\n'.format(counter, section_count))
            for translation in section.translations.all():
                for match in self.regex.finditer(translation.content):
                    uploaded_file = UploadedFile(
                        match.group(3),
                        match.group('year'),
                        match.group('month'),
                        match.group('day'),
                        match.group('filename')
                    )
                    if os.path.exists(uploaded_file.path) and match.group('tag').startswith('<a'):
                        # linked file exists in the mediaroot, move it to the protected root.
                        protected_storage_destination = os.path.join(
                            settings.SENDFILE_ROOT,
                            uploaded_file.year,
                            uploaded_file.month,
                            uploaded_file.filename
                        )
                        try:
                            if not self.dry_run:
                                os.renames(uploaded_file.path, protected_storage_destination)
                        except IOError:
                            self.stdout.write('* Failed to move file {} to {}\n'.format(
                                uploaded_file.path, protected_storage_destination
                            ))
                            continue
                        section_file = SectionFile(section=section)
                        section_file.file.name = os.path.join(
                            uploaded_file.year,
                            uploaded_file.month,
                            uploaded_file.filename
                        )
                        # we have no idea what the file is about, so the file name is our best guess for the Finnish title
                        section_file.set_current_language('fi')
                        section_file.title = uploaded_file.filename
                        if not self.dry_run:
                            section_file.save()
                        self.stdout.write('* Moved {} to {}\n'.format(uploaded_file.path, protected_storage_destination))
                        moved_files[uploaded_file] = section_file
                    if os.path.exists(uploaded_file.path) and match.group('tag').startswith('<img'):
                        # image exists in the mediaroot, move it under images.
                        image_storage_destination = os.path.join(
                            settings.MEDIA_ROOT,
                            'images',
                            uploaded_file.year,
                            uploaded_file.month,
                            uploaded_file.filename
                        )
                        try:
                            if not self.dry_run:
                                os.renames(uploaded_file.path, image_storage_destination)
                        except IOError:
                            self.stdout.write('* Failed to move file {} to {}\n'.format(
                                uploaded_file.path, image_storage_destination
                            ))
                            continue
                        section_image = SectionImage(section=section,
                                                     ordering=SectionImage.objects.filter(section=section).count()+1)
                        section_image.image.name = os.path.join(
                            'images',
                            uploaded_file.year,
                            uploaded_file.month,
                            uploaded_file.filename
                        )
                        if not self.dry_run:
                            section_image.save()
                        self.stdout.write('* Moved {} to {}\n'.format(uploaded_file.path, image_storage_destination))
                        moved_files[uploaded_file] = section_image
                # rewrite urls in content
                for uploaded_file, moved_file in moved_files.items():
                    if uploaded_file.url in translation.content:
                        if type(moved_file) is SectionFile:
                            if self.dry_run:
                                new_url = self.domain + '/dry_run_url/v1/download/1'
                            else:
                                new_url = '{}{}'.format(self.domain, reverse(
                                    'serve_file',
                                    kwargs={'filetype': 'sectionfile', 'pk': moved_file.pk}
                                ))
                        else:
                            new_url = self.domain + moved_file.image.url
                        translation.content = translation.content.replace(uploaded_file.url, new_url)
                        self.stdout.write('* {}: Rewrote URL {} -> {}\n'.format(
                            translation.language_code, uploaded_file.url, new_url
                        ))
                if not self.dry_run:
                    translation.save()




