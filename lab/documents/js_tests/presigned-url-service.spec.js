/*global global*/
import { jest } from "@jest/globals";

import { getCSRFToken, fetchURL } from "../assets/js/presigned-url-service";

describe("Test getCSRFToken", () => {
  it("gets token from cookie", () => {
    document.cookie = "csrftoken=TOKEN";
    const token = getCSRFToken();
    expect(token).toBe("TOKEN");
  });
});

describe("Test fetchURL", () => {
  it("injects CSRF token in request header", () => {
    document.cookie = "csrftoken=TOKEN";
    global.fetch = jest.fn();
    fetchURL("https://test.test");
    expect(global.fetch).toHaveBeenCalledWith("https://test.test", {
      method: "POST",
      headers: new Headers({
        "X-CSRFToken": "TOKEN",
      }),
    });
  });
});
