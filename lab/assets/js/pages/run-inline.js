"use strict";

import {
  dismissAddRelatedRunPopup,
  dismissChangeRelatedRunPopup,
  dismissDeleteRelatedRunPopup,
  onRelatedRunLinkClick,
} from "../run-inline-handlers.js";

// Inspired from django/contrib/admin/static/admin/js/admin/RelatedObjectLookups.js
document.addEventListener("DOMContentLoaded", function () {
  window.dismissAddRelatedRunPopup = dismissAddRelatedRunPopup;
  window.dismissChangeRelatedRunPopup = dismissChangeRelatedRunPopup;
  window.dismissDeleteRelatedRunPopup = dismissDeleteRelatedRunPopup;

  document.querySelectorAll(".related-run-link").forEach((linkEl) => {
    linkEl.addEventListener("click", onRelatedRunLinkClick);
  });
});
