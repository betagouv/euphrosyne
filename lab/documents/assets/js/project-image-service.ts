import { IImagewithUrl } from "../../../../lab_notebook/assets/js/IImageTransform.js";
import { jwtFetch } from "../../../assets/js/jwt.js";
import { UploadSasUrlMixin } from "../../../assets/js/upload-sas-url-mixin";

export class ProjectImageServices extends UploadSasUrlMixin {
  protected projectSlug: string;
  protected uploadSasUrl: string;

  constructor(projectSlug: string) {
    super();
    this.projectSlug = projectSlug;
    this.uploadSasUrl =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `/images/upload/signed-url` +
      `?project_name=${projectSlug}`;
  }

  async listProjectImages(): Promise<IImagewithUrl[]> {
    const url =
      process.env.EUPHROSYNE_TOOLS_API_URL +
      `/images/projects/${this.projectSlug}`;

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
    return this._getUploadSASUrl(`${this.uploadSasUrl}&file_name=${fileName}`);
  }
}
