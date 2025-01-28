import { TypeAheadList } from "../type-ahead-list.component";

export type SearchType = "fullpathSearch" | "autocomplete";

export interface OpenThesoResult {
  id: string;
  arkId: string;
  label: string;
}

export abstract class OpenThesoTypeAhead extends TypeAheadList {
  thesorusId?: string;
  abstract searchType: SearchType;

  async doFetch<T>(query: string): Promise<T[]> {
    if (!this.thesorusId) {
      throw new Error("thesorus-id attribute is required");
    }
    const q = encodeURIComponent(query);

    let url;

    if (this.searchType === "fullpathSearch") {
      url = `https://opentheso.huma-num.fr/openapi/v1/concept/${this.thesorusId}/search/fullpath?q=${q}&lang=fr&exactMatch=false`;
    } else {
      // autocomplete
      url = `https://opentheso.huma-num.fr/openapi/v1/concept/${this.thesorusId}/autocomplete/${q}?lang=fr&exactMatch=false`;
    }
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
    });

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
    return data;
  }
}
