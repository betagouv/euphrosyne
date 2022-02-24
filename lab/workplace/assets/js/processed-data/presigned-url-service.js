"use strict";

import { getCSRFToken } from "../../../../assets/js/utils.js";

export class ProcessedDataPresignedUrlService {
  constructor(projectId, runId) {
    this.projectId = projectId;
    this.runId = runId;
  }

  fetchURL(url) {
    return fetch(url, {
      method: "POST",
      headers: new Headers({
        "X-CSRFToken": getCSRFToken(),
      }),
    });
  }

  async fetchDownloadPresignedURL(key) {
    const response = await this.fetchURL(
      `/api/project/${this.projectId}/workplace/processed_data/presigned_download_url?key=${key}`
    );
    return (await response.json()).url;
  }

  async fetchDeletePresignedURL(key) {
    const response = await this.fetchURL(
      `/api/project/${this.projectId}/workplace/processed_data/presigned_delete_url?key=${key}`
    );
    return (await response.json()).url;
  }

  async fetchListPresignedUrl() {
    const response = await this.fetchURL(
      `/api/project/${this.projectId}/workplace/${this.runId}/processed_data/presigned_list_url`
    );
    return (await response.json()).url;
  }

  async fetchUploadPresignedUrl() {
    const response = await this.fetchURL(
      `/api/project/${this.projectId}/workplace/${this.runId}/processed_data/presigned_post`
    );
    return (await response.json()).url;
  }
}
