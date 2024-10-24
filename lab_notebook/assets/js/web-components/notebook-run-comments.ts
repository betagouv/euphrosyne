import { NotebookServices } from "../notebook.services";

export class NotebookRunComments extends HTMLTextAreaElement {
  services: NotebookServices | undefined;

  static init() {
    customElements.define("notebook-run-comments", NotebookRunComments, {
      extends: "textarea",
    });
  }

  connectedCallback() {
    const runId = this.dataset.runId;

    if (!runId) throw new Error("runId must be defined as element attribute");

    this.services = new NotebookServices(runId);

    this.addEventListener("change", (e) =>
      this.services?.updateRunComments((e.target as HTMLTextAreaElement).value),
    );
  }
}
