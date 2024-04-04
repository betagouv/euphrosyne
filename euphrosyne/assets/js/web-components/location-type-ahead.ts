import { TypeAheadList, Result } from "../type-ahead-list.component";

interface GeonamesResult {
  geonameId: number;
  toponymName: string;
  countryName: string;
  lat: string;
  lng: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
class LocationTypeAhead extends TypeAheadList {
  async fetchResults(query: string): Promise<Result[]> {
    const geonamesUsername = process.env.GEONAMES_USERNAME;
    const response = await fetch(
      `https://secure.geonames.org/searchJSON?username=${geonamesUsername}&q=${encodeURIComponent(query)}&maxRows=15`,
    );

    if (!response || !response.ok) {
      throw new Error("Failed to fetch results");
    }

    return (await response.json()).geonames.map((item: GeonamesResult) => ({
      label: `${item.toponymName}, ${item.countryName}`,
      id: item.geonameId,
      attrs: {
        country: item.countryName,
        name: item.toponymName,
        latitude: item.lat,
        longitude: item.lng,
      },
    }));
  }
}

customElements.define("location-type-ahead", LocationTypeAhead, {
  extends: "div",
});
