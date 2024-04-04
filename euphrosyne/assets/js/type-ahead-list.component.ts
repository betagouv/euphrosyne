export interface Result {
  label: string;
  id: string;
  attrs: object;
}

export abstract class TypeAheadList extends HTMLDivElement {
  abstract fetchResults(query: string): Promise<Result[]>;

  static get observedAttributes() {
    return ["html-for"];
  }

  timeoutId: ReturnType<typeof setTimeout> | undefined;

  connectedCallback() {
    document.addEventListener("click", (event) => {
      // Hide typeahead list when clicking outside
      const isInside = this.contains(event.target as Node);
      if (!isInside && !this.classList.contains("hidden")) {
        this.classList.add("hidden");
      }
    });

    const htmlFor = this.getAttribute("html-for");
    if (!htmlFor) {
      throw new Error("html-for attribute is required");
    }
    const forInputElement = document.getElementById(
      htmlFor,
    ) as HTMLInputElement;
    forInputElement.addEventListener("input", this.onInput.bind(this));
  }

  attributeChangedCallback(name: string, oldValue: string, newValue: string) {
    // We need to watch for changes to the "html-for" attribute
    // when using the widget in inline forms, when clicking the "Add another" button
    if (name !== "html-for") return;
    document
      .getElementById(oldValue)
      ?.removeEventListener("input", this.onInput.bind(this));
    if (name === "html-for") {
      const forInputElement = document.getElementById(
        newValue,
      ) as HTMLInputElement;
      forInputElement.addEventListener("input", this.onInput.bind(this));
    }
  }

  onInput(event: Event) {
    const query = (event.target as HTMLInputElement).value;
    if (query === undefined) {
      return;
    }

    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }

    this.timeoutId = setTimeout(async () => {
      try {
        const results = await this.fetchResults(query);
        if (results.length === 0) {
          this.displayNoResultsBanner();
        } else {
          this.populateResults(results);
        }
      } catch (error) {
        console.error(error);
        this.displayErrorBanner();
      }
    }, 500);
  }

  populateResults(results: Result[]) {
    this.cleanList();
    results.forEach((result) => {
      const button = document.createElement("button");
      button.textContent = result.label;
      button.type = "button";
      button.addEventListener("click", () =>
        this.dispatchEvent(
          new CustomEvent("result-click", { detail: { result: result } }),
        ),
      );
      this.appendChild(button);
      this.classList.remove("hidden");
    });
  }

  cleanList() {
    Array.from(this.children).forEach((el) => {
      el.remove();
    });
  }

  displayErrorBanner() {
    const banner = document.createElement("div");
    banner.textContent = window.gettext(
      "An error occured while fetching results",
    );
    this.cleanList();
    this.appendChild(banner);
    this.classList.remove("hidden");
  }

  displayNoResultsBanner() {
    const banner = document.createElement("div");
    banner.textContent = window.gettext("No results");
    this.cleanList();
    this.appendChild(banner);
    this.classList.remove("hidden");
  }
}
