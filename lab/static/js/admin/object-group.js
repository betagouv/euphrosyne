(function () {
  let groupLabelHiddenInput;
  const getObjectsInline = () => document.getElementById("object_set-group");
  const getGroupLabelRow = () =>
    document.querySelector("fieldset.module div.field-label");

  function setupGroupLabelHiddenInput() {
    groupLabelHiddenInput = document.createElement("input");
    groupLabelHiddenInput.type = "hidden";
    groupLabelHiddenInput.name = "label";
    groupLabelHiddenInput.value = "";
    groupLabelHiddenInput.disabled = true;
    getGroupLabelRow().parentNode.insertBefore(
      groupLabelHiddenInput,
      getGroupLabelRow().nextSibling
    );
  }
  function handleNumObjectsChange(event) {
    /**
     * Toggle form interface between SINGLE OBJECT / OBJECT GROUP.
     * When selecting SINGLE OBJECT, group label input is disabled and
     * replaced by a hidden input ; all object rows are removed except the first
     * one, and the button to add a new one is hidden to prevent
     * adding multiple objects.
     */
    const value = event.target.value;
    const groupLabelRow = getGroupLabelRow();
    if (value === "SINGLE_OBJECT") {
      groupLabelRow.style.display = "none";
      groupLabelRow.querySelector("input").disabled = true;
      groupLabelHiddenInput.disabled = false;

      getObjectsInline().querySelector(".add-row").style.display = "none";
      const newObjectRows = getObjectsInline().querySelectorAll(
        "tr.dynamic-object_set"
      );
      if (newObjectRows.length > 1) {
        newObjectRows.forEach((row, index) => {
          if (index > 0) {
            row.querySelector("a.inline-deletelink").click();
          }
        });
      }
    } else if (value === "OBJECT_GROUP") {
      groupLabelRow.style.display = null;
      groupLabelRow.querySelector("input").disabled = false;
      groupLabelHiddenInput.disabled = true;

      getObjectsInline().querySelector(".add-row").style.display = null;
    }
  }

  document.addEventListener("DOMContentLoaded", function (_) {
    setupGroupLabelHiddenInput();
    document
      .querySelector("input#id_add_type")
      .addEventListener("change", handleNumObjectsChange);
  });
})();
