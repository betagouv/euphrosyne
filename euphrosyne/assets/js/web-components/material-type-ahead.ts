import { Result } from "../type-ahead-list.component";
import {
  OpenThesoResult,
  OpenThesoTypeAhead,
  SearchType,
} from "./open-theso-type-ahead";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class MaterialTypeAhead extends OpenThesoTypeAhead {
  thesorusId = "th291";
  searchType: SearchType = "autocomplete";

  async fetchResults(query: string): Promise<Result[]> {
    const data = await this.doFetch<OpenThesoResult>(query);
    return data.map((item: OpenThesoResult) => ({
      label: item.label,
      id: item.id,
    })) as Result[];
  }
}

customElements.define("material-type-ahead", MaterialTypeAhead, {
  extends: "div",
});
