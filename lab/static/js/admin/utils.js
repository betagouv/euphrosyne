function displayMessage(message, tag) {
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
  document.querySelector("ul.messagelist").appendChild(messageElement);
}
