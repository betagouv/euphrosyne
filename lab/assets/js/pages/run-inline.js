/* global $ */
"use strict";

import "../../css/run-inline.css";

export function dismissAddRelatedRunPopup(win, data) {
  $("#runs-group .inline-related:last").next().find("a").click();
  const inlines = document.querySelectorAll("#runs-group .inline-related");
  const newInline = inlines[inlines.length - 2];
  newInline.querySelector(".inline_label").childNodes[0].data = data.label;
  newInline.querySelector(".inline_label").appendChild(
    new DOMParser().parseFromString(
      `
    <a href="/admin/lab/run/${data.id}/change/?_popup=1" class="inlinechangelink related-run-link">Modification</a>
    `,
      "text/html"
    ).body.firstElementChild
  );
  [
    "start_date",
    "end_date",
    "particle_type",
    "energy_in_keV",
    "beamline",
  ].forEach(function (fieldName) {
    newInline.querySelector(`.field-${fieldName} > div > div`).innerText =
      data[fieldName];
  });
  win.close();
}

export function dismissChangeRelatedRunPopup(win, data) {
  const inline = Array.from(
    document.querySelectorAll("#runs-group .inline-related")
  ).filter(
    (n) =>
      n.querySelector("a.inlinechangelink") &&
      new RegExp(`.*/lab/run/${data.id}/.*`).test(
        n.querySelector("a.inlinechangelink").href
      )
  )[0];
  inline.querySelector(".inline_label").childNodes[0].data = data.label;
  [
    "start_date",
    "end_date",
    "particle_type",
    "energy_in_keV",
    "beamline",
  ].forEach(function (fieldName) {
    inline.querySelector(`.field-${fieldName} > div > div`).innerText =
      data[fieldName];
  });
  win.close();
}

const updateElementIndex = function (el, prefix, ndx) {
  const id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
  const replacement = prefix + "-" + ndx;
  if ($(el).prop("for")) {
    $(el).prop("for", $(el).prop("for").replace(id_regex, replacement));
  }
  if (el.id) {
    el.id = el.id.replace(id_regex, replacement);
  }
  if (el.name) {
    el.name = el.name.replace(id_regex, replacement);
  }
};

export function dismissDeleteRelatedRunPopup(win, id) {
  const inline = Array.from(
    document.querySelectorAll("#runs-group .inline-related")
  ).filter(
    (n) =>
      n.querySelector("a.inlinechangelink") &&
      new RegExp(`.*/lab/run/${id}/.*`).test(
        n.querySelector("a.inlinechangelink").href
      )
  )[0];
  document.getElementById("runs").removeChild(inline);

  // Update the TOTAL_FORMS form count.
  const forms = $(".dynamic-runs");
  $("#id_runs-TOTAL_FORMS").val(forms.length);
  // Also, update names and ids for all remaining form controls so
  // they remain in sequence:
  let i, formCount;
  const updateElementCallback = function () {
    updateElementIndex(this, "runs", i);
  };
  for (i = 0, formCount = forms.length; i < formCount; i++) {
    updateElementIndex($(forms).get(i), "runs", i);
    $(forms.get(i)).find("*").each(updateElementCallback);
  }

  win.close();
}

// Inspired from django/contrib/admin/static/admin/js/admin/RelatedObjectLookups.js
document.addEventListener("DOMContentLoaded", function () {
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

  function showRelatedRunPopup(triggeringLink) {
    return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
  }
  window.dismissAddRelatedRunPopup = dismissAddRelatedRunPopup;
  window.dismissChangeRelatedRunPopup = dismissChangeRelatedRunPopup;
  window.dismissDeleteRelatedRunPopup = dismissDeleteRelatedRunPopup;

  $(document).ready(function () {
    $("body").on("click", ".related-run-link", function (e) {
      e.preventDefault();
      if (this.href) {
        const event = $.Event("django:show-related", { href: this.href });
        $(this).trigger(event);
        if (!event.isDefaultPrevented()) {
          showRelatedRunPopup(this);
        }
      }
    });
  });
});
