(function () {
  let groupLabelHiddenInput;
  const getObjectsInline = () => document.getElementById("objects-group");
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
    const value = event.target.selectedOptions[0].value;
    if (value === "SINGLE_OBJECT") {
      getGroupLabelRow().style.display = "none";
      groupLabelHiddenInput.disabled = false;

      getObjectsInline().querySelector(".add-row").style.display = "none";
      const newObjectRows = getObjectsInline().querySelectorAll(
        "tr.dynamic-object_set"
      );
      if (newObjectRows.length > 1) {
        for (let i = 1; i <= newObjectRows.length; i++) {
          newObjectRows[i].querySelector("a.inline-deletelink").click();
        }
      }
    } else if (value === "OBJECT_GROUP") {
      getGroupLabelRow().style.display = null;
      groupLabelHiddenInput.disabled = true;

      getObjectsInline().querySelector(".add-row").style.display = null;
    }
  }

  document.addEventListener("DOMContentLoaded", function (_) {
    setupGroupLabelHiddenInput();
    document
      .getElementById("id_add_type")
      .addEventListener("change", handleNumObjectsChange);
  });
})();
