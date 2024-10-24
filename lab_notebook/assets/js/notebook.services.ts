import { getCSRFToken } from "../../../lab/assets/js/utils.js";

export class NotebookServices {
  protected runId: string;

  constructor(runId: string) {
    this.runId = runId;
  }

  updateRunComments(comments: string) {
    const headers: HeadersInit = new Headers();
    headers.set("X-CSRFToken", getCSRFToken() || "");
    headers.set("Content-Type", "application/json");

    fetch(`/api/notebook/run-notebook/${this.runId}`, {
      method: "PUT",
      body: JSON.stringify({ comments }),
      headers,
    });
  }
}
