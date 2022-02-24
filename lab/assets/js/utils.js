"use strict";

export function displayMessage(message, tag) {
  /**
   * Displays a message, Django message style.
   * Appends a message to a `ul` element wiht class `messagelist`
   */
  const messageElement = document.createElement("li");
  messageElement.classList.add(tag);
  messageElement.innerText = message;
  const closeElement = document.createElement("span");
  closeElement.innerText = "x";
  closeElement.classList.add("close");
  messageElement.appendChild(closeElement);
  messageElement.addEventListener("click", (event) =>
    (event.target === messageElement
      ? event.target
      : event.target.parentElement
    ).remove()
  );
  document.querySelector("ul.messagelist")?.appendChild(messageElement);
}

export function formatBytes(a, b = 2, k = 1024) {
  /**
   * Format bytes int size.
   * Taken from this SO answer : https://stackoverflow.com/a/18650828/7433420
   */
  const { floor, log, pow, max } = Math;
  let d = floor(log(a) / log(k));
  return 0 == a
    ? "0 B"
    : parseFloat((a / pow(k, d)).toFixed(max(0, b))) +
        " " +
        ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"][d];
}

export function getCSRFToken() {
  // Get CSRF token from cookies
  // https://docs.djangoproject.com/en/4.0/ref/csrf/#ajax
  const cookieName = "csrftoken";
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, cookieName.length + 1) === cookieName + "=") {
        return decodeURIComponent(cookie.substring(cookieName.length + 1));
      }
    }
  }
  return null;
}
