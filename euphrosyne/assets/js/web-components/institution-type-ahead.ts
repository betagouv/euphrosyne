import { TypeAheadList, Result } from "../type-ahead-list.component";

interface RorResult {
  name: string;
  id: string;
  country: {
    country_name: string;
  };
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class InstitutionTypeAhead extends TypeAheadList {
  async fetchResults(query: string): Promise<Result[]> {
    const response = await fetch(
      "https://api.ror.org/organizations?query=" + encodeURIComponent(query),
    );

    if (!response.ok) {
      throw new Error("Failed to fetch results");
    }

    return (await response.json()).items.map((item: RorResult) => ({
      label: `${item.name}, ${item.country.country_name}`,
      id: item.id,
      attrs: { country: item.country.country_name, name: item.name },
    }));
  }
}

customElements.define("institution-type-ahead", InstitutionTypeAhead, {
  extends: "div",
});
