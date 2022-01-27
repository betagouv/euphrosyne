"use strict";

import {
  dismissAddRelatedRunPopup,
  dismissChangeRelatedRunPopup,
  dismissDeleteRelatedRunPopup,
} from "../run-inline-handlers.js";

// Inspired from django/contrib/admin/static/admin/js/admin/RelatedObjectLookups.js
document.addEventListener("DOMContentLoaded", function () {
  window.dismissAddRelatedRunPopup = dismissAddRelatedRunPopup;
  window.dismissChangeRelatedRunPopup = dismissChangeRelatedRunPopup;
  window.dismissDeleteRelatedRunPopup = dismissDeleteRelatedRunPopup;

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

  function showRelatedRunPopup(triggeringLink) {
    return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
  }

  document.querySelectorAll(".related-run-link").forEach((linkEl) => {
    linkEl.addEventListener("click", function (e) {
      e.preventDefault();
      if (this.href) {
        const event = new Event("django:show-related");
        event.href = this.href;
        document.dispatchEvent(event);
        if (!event.defaultPrevented) {
          showRelatedRunPopup(this);
        }
      }
    });
  });
});
