import { IImagewithUrl } from "../../../../lab_notebook/assets/js/IImageTransform.js";
import { UploadSasUrlMixin } from "../../../assets/js/upload-sas-url-mixin";

export class ProjectImageServices extends UploadSasUrlMixin {
  protected projectSlug: string;
  protected uploadSasUrl: string;

  constructor(projectSlug: string, fetchFn?: typeof fetch) {
    super(fetchFn);
    this.projectSlug = projectSlug;
    this.uploadSasUrl =
      `/images/upload/signed-url` + `?project_name=${projectSlug}`;
  }

  async listProjectImages(sasToken?: string): Promise<IImagewithUrl[]> {
    const url = `/images/projects/${this.projectSlug}?with_sas_token=${!sasToken}`;

    const requestInit: RequestInit = {
      method: "GET",
    };

    let response: Response | undefined;

    try {
      response = await this.fetchFn(url, requestInit);
    } catch (error) {
      console.error(error);
      return [];
    }

    const images = (await response?.json()) as { images: string[] } | undefined;

    if (images) {
      return images.images.map((image) => ({
        url: sasToken ? image + "?" + sasToken : image, // assume there is no query string in the image url
        transform: undefined,
        provider: "euphrosyne",
      }));
    }
    return [];
  }

  async getUploadSASUrl(fileName: string) {
    return this._getUploadSASUrl(`${this.uploadSasUrl}&file_name=${fileName}`);
  }
}
