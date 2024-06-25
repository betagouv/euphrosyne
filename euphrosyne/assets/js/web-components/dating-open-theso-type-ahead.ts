import { Result } from "../type-ahead-list.component";
import {
  OpenThesoTypeAhead,
  SearchType,
  OpenThesoResult,
} from "./open-theso-type-ahead";

export class DatingOpenThesoTypeAhead extends OpenThesoTypeAhead {
  searchType: SearchType = "fullpathSearch";

  connectedCallback(): void {
    this.thesorusId = this.getAttribute("thesorus-id") || "";
    super.connectedCallback();
  }

  async fetchResults(query: string): Promise<Result[]> {
    const data = await this.doFetch<OpenThesoResult[]>(query);
    return data.map((item: OpenThesoResult[]) => ({
      label: item.map((i) => i.label).join(" > "),
      id: item.slice(-1)[0].id,
    })) as Result[];
  }
}

customElements.define(
  "dating-open-theso-type-ahead",
  DatingOpenThesoTypeAhead,
  {
    extends: "div",
  },
);
