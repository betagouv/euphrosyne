import { TypeAheadList, Result } from "../type-ahead-list.component";

interface OpenThesoResult {
  id: string;
  arkId: string;
  label: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class MaterialTypeAhead extends TypeAheadList {
  async fetchResults(query: string): Promise<Result[]> {
    const q = encodeURIComponent(query);
    const response = await fetch(
      `https://opentheso.huma-num.fr/opentheso/openapi/v1/concept/th291/autocomplete/${q}?lang=fr&exactMatch=false`,
    );

    if (response && response.status === 404) {
      return [];
    }
    if (!response || !response.ok) {
      throw new Error("Failed to fetch results");
    }

    const data = await response.json();
    if (!data || !data.length) {
      return [];
    }
    return data.map((item: OpenThesoResult) => ({
      label: item.label,
      id: item.id,
    }));
  }
}

customElements.define("material-type-ahead", MaterialTypeAhead, {
  extends: "div",
});
