"use strict";

import { displayMessage, formatBytes, getCSRFToken } from "../assets/js/utils";

test("displays message", () => {
  document.body.innerHTML = '<ul class="messagelist"></ul>';
  displayMessage("hello", "success");
  expect(document.querySelector("ul.messagelist").children.length).toBe(1);
  expect(
    document.querySelector("ul.messagelist").firstElementChild.innerText
  ).toMatch("hello");
});

test("formatBytes function", () => {
  const inputOutputMapping = [
    [0, "0 B"],
    [55, "55 B"],
    [1024, "1 KB"],
    [1600, "1.56 KB"],
    [1048576, "1 MB"],
    [1236576, "1.18 MB"],
    [1073741824, "1 GB"],
    [5374677263, "5.01 GB"],
  ];
  const results = inputOutputMapping.map(([input]) => [
    input,
    formatBytes(input),
  ]);
  expect(results).toStrictEqual(inputOutputMapping);
});

describe("Test getCSRFToken", () => {
  it("gets token from cookie", () => {
    document.cookie = "csrftoken=TOKEN";
    const token = getCSRFToken();
    expect(token).toBe("TOKEN");
  });
});
