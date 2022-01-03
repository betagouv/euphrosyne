"use strict";

const { expect } = require("@jest/globals");
const { displayMessage } = require("../../static/js/admin/utils");

test("displays message", () => {
  document.body.innerHTML = '<ul class="messagelist"></ul>';
  displayMessage("hello", "success");
  expect(document.querySelector("ul.messagelist").children.length).toBe(1);
  expect(
    document.querySelector("ul.messagelist").firstElementChild.innerText
  ).toMatch("hello");
});
