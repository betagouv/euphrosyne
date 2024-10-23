import { jwtFetch } from "../../../lab/assets/js/jwt.js";
import { UploadSasUrlMixin } from "../../../lab/assets/js/upload-sas-url-mixin";
import { getCSRFToken } from "../../../lab/assets/js/utils.js";
import { IRunObjectImage } from "./IImageTransform.js";

export class StorageImageServices {
  protected projectSlug: string;

  constructor(projectSlug: string) {
    this.projectSlug = projectSlug;
  }

  async getImagesUrlAndToken() {
    const url =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `/images/projects/${this.projectSlug}/signed-url`;

    const response = await jwtFetch(url);

    if (!response?.ok) {
      console.error(response);
      throw new Error(
        window.gettext("An error occured while requesting upload URL."),
      );
    }

    const { base_url, token } = (await response.json()) as {
      base_url: string;
      token: string;
    };
    return {
      baseUrl: base_url,
      token: token,
    };
  }
}

export class ObjectGroupImageServices extends UploadSasUrlMixin {
  protected projectSlug: string;
  protected objectGroupId: string;
  protected uploadSasUrl: string;

  constructor(projectSlug: string, objectGroupId: string) {
    super();
    this.projectSlug = projectSlug;
    this.objectGroupId = objectGroupId;
    this.uploadSasUrl =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `/images/upload/signed-url` +
      `?project_name=${projectSlug}&object_group_id=${objectGroupId}`;
  }

  async getUploadSASUrl(fileName: string) {
    return this._getUploadSASUrl(
      `${this.uploadSasUrl}&object_group_id=${this.objectGroupId}&file_name=${fileName}`,
    );
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
