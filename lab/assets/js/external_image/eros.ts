import { getToken } from "../../../../shared/js/jwt";
import { ExternalImageProvider } from "./types";

export const EROS_BASE_URL = `${process.env.EUPHROSYNE_TOOLS_API_URL}/eros`;

interface ErosImage {
  filmnbr: string;
  worknbr: string;
  czone: string;
  aimfilm: string;
  technique: string;
  dtfilm: string;
  caimfilm: string | undefined;
  plfilm: string;
  opfilm: string;
  owner: string;
  stock: string;
  filmtype: string;
  zone: string;
  Xsize: string;
  Ysize: string;
  bands: string;
}

interface ErosObject {
  title: string;
  local: string;
  owner: string;
  worknbr: string;
  collection: string;
  dtfrom: string;
  dtto: string;
  appel: string;
  support: string;
  technique: string;
  height: string;
  width: string;
  workgroup: string;
  srmf: string;
  categ: string;
  images: ErosImage[] | null;
}

function constructFromPath(path: string, token?: string) {
  const [erosId, imageId] = path.split("/");
  let imageCategory: string;
  if (erosId.startsWith("C2RMF")) {
    imageCategory = `pyr-${erosId.substring(0, 6)}`;
  } else if (erosId.startsWith("F")) {
    imageCategory = `pyr-${erosId.substring(0, 2)}`;
  } else {
    imageCategory = `pyr-FZ`;
  }
  let url = `${EROS_BASE_URL}/iiif/${imageCategory}/${erosId}/${imageId}.tif/full/500,/0/default.jpg`;
  if (token) {
    url = `${url}?token=${token}`;
  }
  return url;
}

async function getImagesURLForObject(providerObjectId: string) {
  const objectDetailsURL = `${EROS_BASE_URL}/rails/oeuvres/${providerObjectId}.json`;
  let fetchFailed = false,
    objectResponse: Response | undefined = undefined;
  const token = await getToken();
  try {
    objectResponse = await fetch(`${objectDetailsURL}?token=${token}`);
  } catch (error) {
    console.error(error);
    fetchFailed = true;
  }
  if (fetchFailed || (objectResponse && !objectResponse.ok)) {
    console.warn(
      `Failed to fetch object details with id ${providerObjectId}.\n
        URL: ${objectDetailsURL}\n`,
    );
    if (objectResponse && !objectResponse.ok) {
      console.warn(`
        Status: ${objectResponse.statusText}\n
        Content: ${await objectResponse.text()}`);
    }
    return [];
  }
  if (objectResponse) {
    const objectDetails = (await objectResponse.json()) as ErosObject;
    if (!objectDetails.images || objectDetails.images.length === 0) {
      console.warn(`No images found for object with id ${providerObjectId}`);
      return [];
    }
    return objectDetails.images.map((image) =>
      constructFromPath(`${providerObjectId}/${image.filmnbr}`, token),
    );
  }
  return [];
}

export const erosImageService: ExternalImageProvider = {
  getImagesURL: (providerObjectId: string) =>
    getImagesURLForObject(providerObjectId),
  constructFromPath: (path: string, token?: string) =>
    constructFromPath(path, token),
};
