import { TypeAheadList, Result } from "../type-ahead-list.component";

interface OpentThesoResult {
  id: string;
  arkId: string;
  label: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class PeriodTypeAhead extends TypeAheadList {
  async fetchResults(query: string): Promise<Result[]> {
    const q = encodeURIComponent(query);
    const response = await fetch(
      `https://opentheso.huma-num.fr/opentheso/openapi/v1/concept/th289/search/fullpath?q=${q}&lang=fr&exactMatch=false`,
    );

    if (!response || !response.ok) {
      throw new Error("Failed to fetch results");
    }

    const data = await response.json();
    if (!data || !data.length) {
      return [];
    }
    return data.map((item: OpentThesoResult[]) => ({
      label: item.map((i) => i.label).join(" > "),
      id: item.slice(-1)[0].id,
    }));
  }
}

customElements.define("period-type-ahead", PeriodTypeAhead, {
  extends: "div",
});
