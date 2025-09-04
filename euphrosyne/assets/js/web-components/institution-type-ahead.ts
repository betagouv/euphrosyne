import { TypeAheadList, Result } from "../type-ahead-list.component";

interface RorResult {
  id: string;
  names: {
    lang: string;
    types: string[];
    value: string;
  }[];
  locations: {
    geonames_details: {
      country_name: string;
    };
  }[];
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class InstitutionTypeAhead extends TypeAheadList {
  constructor() {
    super();

    // Empty message ROR registration link
    this.emptyResultMessageElement = document.createElement("span");
    this.emptyResultMessageElement.textContent =
      window.gettext(
        "No results found. You can register a new institution using",
      ) + " ";
    const link = document.createElement("a");
    link.target = "_blank";
    link.href =
      "https://docs.google.com/forms/d/e/1FAIpQLSdJYaMTCwS7muuTa-B_CnAtCSkKzt19lkirAKG4u7umH9Nosg/viewform";
    link.textContent = window.gettext("this form");
    this.emptyResultMessageElement.appendChild(link);
  }

  async fetchResults(query: string): Promise<Result[]> {
    const response = await fetch(
      "https://api.ror.org/organizations?query=" + encodeURIComponent(query),
    );

    if (!response.ok) {
      throw new Error("Failed to fetch results");
    }

    return (await response.json()).items.map((item: RorResult) => {
      console.log(item.locations[0]);
      return {
        label: `${item.names[0].value}, ${item.locations[0].geonames_details.country_name}`,
        id: item.id,
        attrs: {
          country: item.locations[0].geonames_details.country_name,
          name: item.names[0].value,
        },
      };
    });
  }
}

customElements.define("institution-type-ahead", InstitutionTypeAhead, {
  extends: "div",
});
