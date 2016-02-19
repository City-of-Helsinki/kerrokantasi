// Fix ckeditor of dynamically added nested inlines.
// The ckeditor related code is copied from django-ckeditor init.
(function($) {
    $(document).on('djnesting:added', function() {
        $('textarea[data-type=ckeditortype]').each(function() {
            if($(this).data('processed') == "0" && $(this).attr('id').indexOf('__prefix__') == -1) {
                $(this).data('processed', "1");
                $($(this).data('external-plugin-resources')).each(function() {
                    CKEDITOR.plugins.addExternal(this[0], this[1], this[2]);
                });
                CKEDITOR.replace($(this).attr('id'), $(this).data('config'));
            }
        });
    });
})(django.jQuery);