"use strict";

import { displayMessage } from "../assets/js/utils";
import { expect } from "@jest/globals";

test("displays message", () => {
  document.body.innerHTML = '<ul class="messagelist"></ul>';
  displayMessage("hello", "success");
  expect(document.querySelector("ul.messagelist").children.length).toBe(1);
  expect(
    document.querySelector("ul.messagelist").firstElementChild.innerText
  ).toMatch("hello");
});
