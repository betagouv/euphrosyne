/*global SelectBox, interpolate*/
// Inspired from django/contrib/admin/static/admin/js/admin/RelatedObjectLookups.js
"use strict";
{
  const $ = django.jQuery;

  function showAdminPopup(triggeringLink, name_regexp, add_popup) {
    const name = triggeringLink.id.replace(name_regexp, "");
    const href = new URL(triggeringLink.href);
    if (add_popup) {
      href.searchParams.set("_popup", 1);
    }
    const win = window.open(
      href,
      name,
      "height=500,width=800,resizable=yes,scrollbars=yes"
    );
    win.focus();
    return false;
  }
  function showRelatedObjectPopup(triggeringLink) {
    return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
  }

  function dismissViewObjectPopup(win, newRepr, newId) {
    const id = win.name.replace(/^view_/, "");
    const selectsSelector = interpolate("#%s, #%s_from, #%s_to", [id, id, id]);
    $("#" + id).text(newRepr);
    win.close();
  }
  window.dismissViewObjectPopup = dismissViewObjectPopup;

  $(document).ready(function () {
    $("body").on("click", ".popup-view-link", function (e) {
      e.preventDefault();
      if (this.href) {
        const event = $.Event("django:show-related", { href: this.href });
        $(this).trigger(event);
        if (!event.isDefaultPrevented()) {
          showRelatedObjectPopup(this);
        }
      }
    });
  });
}
