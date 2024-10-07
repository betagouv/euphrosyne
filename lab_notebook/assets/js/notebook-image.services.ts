import { jwtFetch } from "../../../lab/assets/js/jwt.js";
import { getCSRFToken } from "../../../lab/assets/js/utils.js";
import {
  IRunObjectImage,
  IImageTransform,
  IImagewithUrl,
} from "./IImageTransform.js";

export class ObjectGroupImageServices {
  protected projectSlug: string;
  protected objectGroupId: string;

  constructor(projectSlug: string, objectGroupId: string) {
    this.projectSlug = projectSlug;
    this.objectGroupId = objectGroupId;
  }

  async listObjectGroupImages(): Promise<IImagewithUrl[]> {
    const url =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `/images/projects/${this.projectSlug}/object-groups/${this.objectGroupId}`;

    const requestInit: RequestInit = {
      method: "GET",
    };

    let response: Response | undefined;

    try {
      response = await jwtFetch(url, requestInit);
    } catch (error) {
      console.error(error);
      return [];
    }

    const images = (await response?.json()) as { images: string[] } | undefined;

    if (images) {
      return images.images.map((image) => ({
        url: image,
        transform: undefined,
      }));
    }
    return [];
  }

  async getUploadSASUrl(fileName: string) {
    const url =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `/images/upload/signed-url` +
      `?project_name=${this.projectSlug}&object_group_id=${this.objectGroupId}&file_name=${fileName}`;

    let response: Response | undefined;

    response = await jwtFetch(url);

    if (!response) {
      throw new Error(
        window.gettext("An error occured while requesting upload URL."),
      );
    }

    if (!response.ok) {
      const body = (await response.json()) as {
        detail: { error_code?: string; message: string } | string;
      };
      if (typeof body.detail !== "string") {
        if (body.detail.error_code === "extension-not-supported") {
          throw new Error("File extension not supported.");
        } else {
          throw new Error(body.detail.message);
        }
      } else {
        throw new Error(body.detail);
      }
    }

    const data = (await response?.json()) as { url: string } | undefined;

    if (data) {
      return data.url;
    }
    throw new Error(
      window.gettext("Didn't receive upload URL from euphrosyne tools."),
    );
  }

  async getImagesUrlAndToken() {
    const url =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `images/projects/${this.projectSlug}/signed-url`;

    let response: Response | undefined;

    response = await jwtFetch(url);

    if (!response?.ok) {
      console.error(response);
      throw new Error(
        window.gettext("An error occured while requesting upload URL."),
      );
    }

    return (await response.json()) as { url: string; token: string };
  }
}

export class RunObjectGroupImageServices {
  protected runObjectGroupId: string;

  constructor(runObjectGroupId: string) {
    this.runObjectGroupId = runObjectGroupId;
  }

  async listRunObjectGroupImages() {
    let response;

    try {
      response = await fetch(
        `/api/lab/run_objectgroups/${this.runObjectGroupId}/images`,
      );
    } catch (error) {
      console.error(error);
      return [];
    }
    if (!response || !response.ok) {
      console.error(
        `Error in response while fetching run object group images.`,
        response,
      );
      return [];
    }

    return (await response.json()) as IRunObjectImage[];
  }

  async addRunObjectGroupImage(
    image: IRunObjectImage,
  ): Promise<IRunObjectImage> {
    const headers: HeadersInit = new Headers();
    headers.set("X-CSRFToken", getCSRFToken() || "");
    headers.set("Content-Type", "application/json");

    const { path, transform } = image;

    const response = await fetch(
      `/api/lab/run_objectgroups/${this.runObjectGroupId}/images`,
      {
        method: "POST",
        body: JSON.stringify({ path, transform }),
        headers,
      },
    );

    if (!response || !response.ok) {
      throw new Error("Error while adding image to run object group.");
    }

    const { id } = (await response.json()) as { id: number };
    return { ...image, id: id.toString() };
  }
}
