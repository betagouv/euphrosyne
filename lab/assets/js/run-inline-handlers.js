export function onRelatedRunLinkClick(e) {
  const showAdminPopup = (triggeringLink, name_regexp, add_popup) => {
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
  };

  e.preventDefault();
  if (e.target.href) {
    const event = new Event("django:show-related");
    event.href = e.target.href;
    document.dispatchEvent(event);
    if (!event.defaultPrevented) {
      return showAdminPopup(e.target, /^(change|add|delete)_/, false);
    }
  }
}

export function dismissAddRelatedRunPopup(win, data) {
  document.querySelector("#runs > .add-row > a").click();
  const inlines = document.querySelectorAll("#runs-group .inline-related");
  const newInline = inlines[inlines.length - 2];
  newInline.querySelector(".inline_label").childNodes[0].data = data.label;
  const relatedRunLink = newInline.querySelector(".inline_label").appendChild(
    new DOMParser().parseFromString(
      `
    <a href="/admin/lab/run/${data.id}/change/?_popup=1" class="inlinechangelink related-run-link">Modification</a>
    `,
      "text/html"
    ).body.firstElementChild
  );

  relatedRunLink.addEventListener("click", onRelatedRunLinkClick);

  Object.entries(data)
    .filter(([fieldName]) => fieldName != "id" && fieldName != "label")
    .forEach(([fieldName, value]) => {
      newInline.querySelector(`.field-${fieldName} > div > div`).textContent =
        value;
    });
  win.close();
}

export function dismissChangeRelatedRunPopup(win, data) {
  const inline = Array.from(
    document.querySelectorAll("#runs-group .inline-related")
  ).filter(
    (n) =>
      !!n.querySelector(
        `a.inlinechangelink[href="/admin/lab/run/${data.id}/change/?_popup=1"]`
      )
  )[0];
  inline.querySelector(".inline_label").childNodes[0].data = data.label;
  Object.entries(data)
    .filter(([fieldName]) => fieldName != "id" && fieldName != "label")
    .forEach(([fieldName, value]) => {
      inline.querySelector(`.field-${fieldName} > div > div`).textContent =
        value;
    });
  win.close();
}

const updateElementIndex = function (el, prefix, ndx) {
  const id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
  const replacement = prefix + "-" + ndx;

  if (el.hasAttribute("for")) {
    el.setAttribute(
      "for",
      el.getAttribute("for").replace(id_regex, replacement)
    );
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
      !!n.querySelector(
        `a.inlinechangelink[href="/admin/lab/run/${id}/change/?_popup=1"]`
      )
  )[0];
  document.getElementById("runs").removeChild(inline);

  // Update the TOTAL_FORMS form count.
  const forms = document.querySelectorAll(".dynamic-runs");
  document.querySelector("#id_runs-TOTAL_FORMS").value = forms.length;
  // Also, update names and ids for all remaining form controls so
  // they remain in sequence:
  forms.forEach((form, index) => {
    updateElementIndex(forms[index], "runs", index);
    const updateElementCallback = (el) => {
      updateElementIndex(el, "runs", index);
    };
    Array.from(form.getElementsByTagName("*")).forEach(updateElementCallback);
  });

  win.close();
}
