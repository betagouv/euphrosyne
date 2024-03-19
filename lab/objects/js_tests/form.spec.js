"use strict";

import { template } from "./html-templates/object-group-form";
import { template as inlineRowsWithCollectionAndInventoryTemplate } from "./html-templates/inline-rows-with-collection-inventory";
import {
  displayObjectGroupForm,
  displaySingleObjectForm,
  updateObjectRows,
  toggleInlineInputsDisabledOnParentChange,
} from "../assets/js/object/form.js";

describe("Test object form module", function () {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  describe("Test displayObjectGroupForm", function () {
    beforeEach(() => {
      document.body.innerHTML = template;
    });

    it("displays correctly the form", function () {
      displayObjectGroupForm();
      const objectCountInput = document.getElementById("id_object_count"),
        objectCountField = document.querySelector(".field-object_count"),
        objectsInlineFieldset = document.getElementById("object_set-fieldset"),
        accordionButton = document.querySelector(
          'button[aria-controls="differentiation-accordion"]',
        );
      expect(objectCountInput.value).toBe("2");
      expect(objectCountInput.getAttribute("min")).toBe("2");
      expect(objectCountInput.getAttribute("type")).toBe("number");
      expect(!objectCountField.classList.contains("hidden")).toBeTruthy();
      expect(!objectsInlineFieldset.classList.contains("hidden")).toBe(true);
      expect(accordionButton.getAttribute("aria-expanded")).toBe("false");
    });

    it("does not update object count if its value is higher than 2", function () {
      document.getElementById("id_object_count").value = 3;
      displayObjectGroupForm();
      expect(document.getElementById("id_object_count").value).toBe("3");
    });
  });

  describe("Test displaySingleObjectForm", function () {
    beforeEach(() => {
      document.body.innerHTML = template;
    });

    it("displays correctly the form", function () {
      // First display object group form
      displayObjectGroupForm();
      displaySingleObjectForm();

      const objectCountInput = document.getElementById("id_object_count");
      expect(objectCountInput.value).toBe("1");
      expect(objectCountInput.getAttribute("min")).toBe("1");
      expect(objectCountInput.getAttribute("min")).toBe("1");
      expect(
        document
          .querySelector(".field-object_count")
          .classList.contains("hidden"),
      ).toBe(true);
      expect(
        document
          .getElementById("object_set-fieldset")
          .classList.contains("hidden"),
      ).toBe(true);
      expect(
        document.querySelectorAll(
          "#object_set-group tbody tr.dynamic-object_set",
        ).length,
      ).toBe(0);
    });
  });

  describe("Test updateObjectRows", function () {
    it("click on add button to add rows", function () {
      document.body.innerHTML = template;
      let clickCount = 0;
      displayObjectGroupForm();
      document
        .querySelector("#object_set-group tr.add-row a")
        .addEventListener("click", () => (clickCount += 1));
      updateObjectRows(50);
      expect(clickCount).toBe(50);
    });
  });

  describe("Test toggleInlineInputsDisabledOnParentChange", function () {
    beforeEach(() => {
      document.body.innerHTML = inlineRowsWithCollectionAndInventoryTemplate;
    });

    it("disables collection inputs", function () {
      toggleInlineInputsDisabledOnParentChange("collection", "abc");
      expect(
        document.getElementById("id_object_set-0-collection").disabled,
      ).toBeTruthy();
      expect(
        document.getElementById("id_object_set-1-collection").disabled,
      ).toBeTruthy();
    });

    it("enables collection inputs", function () {
      document.getElementById("id_object_set-0-collection").disabled = true;
      document.getElementById("id_object_set-1-collection").disabled = true;
      document.body.innerHTML = inlineRowsWithCollectionAndInventoryTemplate;
      toggleInlineInputsDisabledOnParentChange("collection", "");
      expect(
        document.getElementById("id_object_set-0-collection").disabled,
      ).toBeFalsy();
      expect(
        document.getElementById("id_object_set-1-collection").disabled,
      ).toBeFalsy();
    });

    it("disables inventory inputs", function () {
      toggleInlineInputsDisabledOnParentChange("inventory", "abc");
      expect(
        document.getElementById("id_object_set-0-inventory").disabled,
      ).toBeTruthy();
      expect(
        document.getElementById("id_object_set-1-inventory").disabled,
      ).toBeTruthy();
    });

    it("enables collection inputs", function () {
      document.getElementById("id_object_set-0-inventory").disabled = true;
      document.getElementById("id_object_set-1-inventory").disabled = true;
      document.body.innerHTML = inlineRowsWithCollectionAndInventoryTemplate;
      toggleInlineInputsDisabledOnParentChange("inventory", "");
      expect(
        document.getElementById("id_object_set-0-inventory").disabled,
      ).toBeFalsy();
      expect(
        document.getElementById("id_object_set-1-inventory").disabled,
      ).toBeFalsy();
    });
  });
});
