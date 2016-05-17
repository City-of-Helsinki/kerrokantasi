(function($) {
    $(function() {
        function setPluginFieldsVisibility($typeSelect) {
            var $pluginFields = $typeSelect.closest("fieldset").children().has("*[id *=plugin]");

            // hide plugin fields if type select's value is "introduction"
            $typeSelect.val() === "1" ? $pluginFields.hide() : $pluginFields.show();
        }

        // match all section type selects
        $("select[id ^=id_sections-][id $=-type]").each(function() {
            setPluginFieldsVisibility($(this));
            $(this).change(function() {
                setPluginFieldsVisibility($(this));
            });
        });
    });
})(django.jQuery);
