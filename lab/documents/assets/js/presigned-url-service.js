"use strict";

import { jwtFetch } from "../../../assets/js/jwt.js";

export class DocumentPresignedUrlService {
  constructor() {}

  async fetchPresignedURL(projectName) {
    const response = jwtFetch(
      `${process.env.EUPHROSYNE_TOOLS_API_URL}/data/{project_name}/runs/{run_name}/{data_type}/shared_access_signature/{file_name}`,
      {
        method: "GET",
      }
    );
    return (await response.json()).url;
  }
}
