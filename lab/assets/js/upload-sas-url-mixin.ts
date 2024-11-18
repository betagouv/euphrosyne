export class UploadSasUrlMixin {
  fetchFn: typeof fetch;

  constructor(fetchFn?: typeof fetch) {
    this.fetchFn = fetchFn || fetch;
  }

  async _getUploadSASUrl(url: string) {
    const response = await this.fetchFn(url);

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
}
