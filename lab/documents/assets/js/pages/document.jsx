import React from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

import { DocumentFileService } from "../document-file-service";

import FileManager from "../../../../assets/js/components/file-manager.jsx";

const container = document.getElementById("project-documents");

const queryClient = new QueryClient();

const App = () => {
  const documentService = new DocumentFileService(
    window.projectName,
    window.projectSlug
  );

  const formAttrs = JSON.parse(
    container.getAttribute("file-upload-form-attrs").replaceAll("'", '"')
  );
  return (
    <div>
      <ul className="messagelist"></ul>
      <FileManager
        fileService={documentService}
        title={window.gettext("Documents")}
        queryKey="fetch-documents"
        hintText={formAttrs.hint_text}
      />
    </div>
  );
};

const root = createRoot(container);
root.render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);
