(function() {
  var $ = window.jQuery = django.jQuery; // Re-conflict noconflict.

  function initializeSkin(jQuery) {
    WYMeditor.SKINS.djangoadmin = {
      init: function(wym) {
        var containersAndClasses = wym._options.classesSelector + ', ' + wym._options.containersSelector;
        jQuery(wym._box).find(containersAndClasses).addClass("wym_panel");
        jQuery(wym._box).find(wym._options.toolsSelector).addClass("wym_buttons");
      }
    };
  }

  $(function() {
    initializeSkin($);
    $("textarea[data-wym]").each(function() {
      var textarea = this;
      var $textarea = $(textarea);
      $textarea.siblings("label").css("float", "none");
      $textarea.wymeditor({
        skin: 'djangoadmin',
        iframeBasePath: window.__admin_media_prefix__ + "wymeditor/iframe/pretty/",
        basePath: window.__admin_media_prefix__ + "wymeditor/",
      });
    });
    $("input[type=submit]").addClass("wymupdate");
  });
}());
