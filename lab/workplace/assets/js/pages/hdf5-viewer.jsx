import React from "react";
import { BrowserRouter } from "react-router-dom";
import { App, H5GroveProvider } from "@h5web/app";
import { useLocation } from "react-router-dom";
import ReactDom from "react-dom";
import { getToken } from "../../../../assets/js/jwt";
import "@h5web/app/styles.css";

function createAxiosResponseInterceptor(axiosInstance) {
  // When response code is 401, try to refresh the token. Eject the interceptor so it doesn't loop in case
  // token refresh causes the 401 response. Must be re-attached later on or the token refresh will only happen once
  // Taken from : https://stackoverflow.com/a/53294310/7433420
  const interceptor = axiosInstance.interceptors.response.use(
    (response) => response,
    (error) => {
      // Reject promise if usual error
      if (error.response.status !== 401) {
        return Promise.reject(error);
      }
      axiosInstance.interceptors.response.eject(interceptor);
      return getToken(false)
        .then((token) => {
          error.response.config.headers["Authorization"] = "Bearer " + token;
          // Retry the initial call, but with the updated token in the headers.
          // Resolves the promise if successful
          return axiosInstance(error.response.config);
        })
        .finally(() => createAxiosResponseInterceptor(axiosInstance)); // Re-attach the interceptor by running the method
    }
  );
}

function HDF5ViewerApp() {
  const search = useLocation().search;
  const file = new URLSearchParams(search).get("file");

  const h5webApp = App({ explorerOpen: false });

  const h5GroveProvider = H5GroveProvider({
    url: `${process.env.EUPHROSYNE_TOOLS_API_URL}/hdf5`,
    filepath: file,
    axiosConfig: { params: { file } },
    children: h5webApp,
  });

  h5GroveProvider.props.api.client.interceptors.request.use(async (config) => {
    const token = await getToken();
    config.headers["Authorization"] = "Bearer " + token;
    return config;
  });
  createAxiosResponseInterceptor(h5GroveProvider.props.api.client);

  return h5GroveProvider;
}

const container = document.getElementById("root");
ReactDom.render(
  <BrowserRouter>
    <HDF5ViewerApp />
  </BrowserRouter>,
  container
);
