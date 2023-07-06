import React from "react";
import { BrowserRouter } from "react-router-dom";
import { App, H5GroveProvider } from "@h5web/app";
import { useLocation } from "react-router-dom";
import { createRoot } from "react-dom/client";

import "@h5web/app/styles.css";

function HDF5ViewerApp() {
  const search = useLocation().search;
  const file = new URLSearchParams(search).get("file");

  return (
    <H5GroveProvider
      url="http://localhost:8001/hdf5"
      filepath={file}
      axiosConfig={{ params: { file, projectName: window.projectName } }}
    >
      <App explorerOpen={false} />
    </H5GroveProvider>
  );
}

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
  <BrowserRouter>
    <HDF5ViewerApp />
  </BrowserRouter>
);
