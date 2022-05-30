import os

from PIL import Image
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ckeditor_uploader.backends import registry
from ckeditor_uploader import utils
from ckeditor_uploader.views import get_files_browse_urls, ImageUploadView, SearchForm
from django.utils.html import escape
from democracy.views.section import RootFileSerializer


class AbsoluteUrlImageUploadView(ImageUploadView):
    http_method_names = ['post']

    def post(self, request, **kwargs):
        """
        Uploads a file and send back its URL to CKEditor.

        Exactly the same as in django-ckeditor 5.0.3 except that creates
        absolute URLs instead of relative ones.
        """
        uploaded_file = request.FILES['upload']

        backend = registry.get_backend()
        ck_func_num = escape(request.GET['CKEditorFuncNum'])

        # Throws an error when an non-image file are uploaded.
        if not getattr(settings, 'CKEDITOR_ALLOW_NONIMAGE_FILES', True):
            try:
                backend.image_verify(uploaded_file)
            except utils.NotAnImageException:
                return HttpResponse("""
                    <script type='text/javascript'>
                    window.parent.CKEDITOR.tools.callFunction({0}, '', 'Invalid file type.');
                    </script>""".format(ck_func_num))

        section_file = self._save_file(request, uploaded_file)

        url = reverse('serve_file', kwargs={'filetype': 'sectionfile', 'pk': section_file.pk})
        url = request.build_absolute_uri(url)

        # Respond with Javascript sending ckeditor upload url.
        return HttpResponse("""
        <script type='text/javascript'>
            window.parent.CKEDITOR.tools.callFunction({0}, '{1}');
        </script>""".format(ck_func_num, url))

    @staticmethod
    def _save_file(request, uploaded_file):
        """
        Uploaded files are saved to the protected storage.
        """
        data = {
            'file': uploaded_file,
        }
        serializer = RootFileSerializer(data=data, context={})
        if not serializer.is_valid():
            return None
        section_file_obj = serializer.save()

        filename = section_file_obj.file.path

        img_name, img_format = os.path.splitext(filename)
        IMAGE_QUALITY = getattr(settings, "IMAGE_QUALITY", 60)

        if(str(img_format).lower() == "png"):

            img = Image.open(section_file_obj.file.path)
            img = img.resize(img.size, Image.ANTIALIAS)
            img.save("{}.jpg".format(img_name), quality=IMAGE_QUALITY, optimize=True)
            section_file_obj.file.name = section_file_obj.file.name.replace('.png', '.jpg')
            section_file_obj.file.save()

        elif(str(img_format).lower() == "jpg" or str(img_format).lower() == "jpeg"):

            img = Image.open(uploaded_file)
            img = img.resize(img.size, Image.ANTIALIAS)
            img.save(section_file_obj.file.path, quality=IMAGE_QUALITY, optimize=True)

        return section_file_obj


upload = csrf_exempt(AbsoluteUrlImageUploadView.as_view())


def browse(request):
    """
    Uploaded file browse view.

    Exactly the same as in django-ckeditor 5.0.3 except that creates
    absolute URLs instead of relative ones.
    """
    files = get_files_browse_urls(request.user)

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data.get('q', '').lower()
            files = list(filter(lambda d: query in d['visible_filename'].lower(), files))
    else:
        form = SearchForm()

    show_dirs = getattr(settings, 'CKEDITOR_BROWSE_SHOW_DIRS', False)
    dir_list = sorted(set(os.path.dirname(f['src']) for f in files), reverse=True)

    # Ensures there are no objects created from Thumbs.db files - ran across this problem while developing on Windows
    if os.name == 'nt':
        files = [f for f in files if os.path.basename(f['src']) != 'Thumbs.db']

    # this is the only customization to this function
    for f in files:
        f['src'] = request.build_absolute_uri(f['src'])

    context = RequestContext(request, {
        'show_dirs': show_dirs,
        'dirs': dir_list,
        'files': files,
        'form': form
    })
    return render(request, 'ckeditor/browse.html', context)
