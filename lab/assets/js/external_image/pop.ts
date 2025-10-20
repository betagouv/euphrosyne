import { ExternalImageProvider } from "./types";

const POP_IMAGE_URL = "https://pop-perf-assets.s3.gra.io.cloud.ovh.net";

async function getImagesURLForObject(providerObjectId: string) {
  let fetchFailed = false,
    objectResponse: Response | undefined = undefined;

  const url = `/api/lab/objectgroup/provider/pop/images?object_id=${providerObjectId}`;

  try {
    objectResponse = await fetch(url);
  } catch (error) {
    console.error(error);
    fetchFailed = true;
  }
  if (fetchFailed || (objectResponse && !objectResponse.ok)) {
    console.warn(
      `Failed to fetch object details with id ${providerObjectId}.\n
        URL: ${url}\n`,
    );
    if (objectResponse && !objectResponse.ok) {
      console.warn(`
        Status: ${objectResponse.statusText}\n
        Content: ${await objectResponse.text()}`);
    }
    return [];
  }
  if (objectResponse) {
    const content = (await objectResponse.json()) as { images: string[] };
    return content.images;
  }
  return [];
}

function constructFromPath(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${POP_IMAGE_URL}${normalizedPath}`;
}
export const popImageService: ExternalImageProvider = {
  getImagesURL: (providerObjectId: string) =>
    getImagesURLForObject(providerObjectId),
  constructFromPath: (path: string) => {
    return constructFromPath(path);
  },
};
