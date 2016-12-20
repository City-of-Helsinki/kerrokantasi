import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from ckeditor_uploader import image_processing
from ckeditor_uploader import utils
from ckeditor_uploader.views import get_files_browse_urls, ImageUploadView, SearchForm
from django.utils.html import escape


class AbsoluteUrlImageUploadView(ImageUploadView):
    http_method_names = ['post']

    def post(self, request, **kwargs):
        """
        Uploads a file and send back its URL to CKEditor.

        Exactly the same as in django-ckeditor 5.0.3 except that creates
        absolute URLs instead of relative ones.
        """
        uploaded_file = request.FILES['upload']

        backend = image_processing.get_backend()
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

        saved_path = self._save_file(request, uploaded_file)
        self._create_thumbnail_if_needed(backend, saved_path)
        url = utils.get_media_url(saved_path)

        # this is the only customization to this function
        url = request.build_absolute_uri(url)

        # Respond with Javascript sending ckeditor upload url.
        return HttpResponse("""
        <script type='text/javascript'>
            window.parent.CKEDITOR.tools.callFunction({0}, '{1}');
        </script>""".format(ck_func_num, url))


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
    return render_to_response('ckeditor/browse.html', context)
