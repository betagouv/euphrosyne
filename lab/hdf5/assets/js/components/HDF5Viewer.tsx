import { App, H5GroveProvider, createAxiosFetcher } from "@witoldw/h5web-app";
import { getToken } from "../../../../../shared/js/jwt";
import { useEffect, useState } from "react";
import axios, { Axios } from "axios";

function createAxiosResponseInterceptor(axiosInstance: Axios) {
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
          // Retry the initial call with updated headers.
          return axiosInstance.request(error.response.config);
        })
        .finally(() => createAxiosResponseInterceptor(axiosInstance)); // Re-attach the interceptor by running the method
    },
  );
}

export default function HDF5Viewer() {
  const [search, setSearch] = useState(window.location.search);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setSearch(window.location.search);
  }, [window.location]);

  useEffect(() => {
    getToken().then(setToken);
  }, []);

  const h5webApp = App({ sidebarOpen: true });

  const file = new URLSearchParams(search).get("file");

  const axiosInstance = axios.create({
    headers: { Authorization: `Bearer ${token}` },
    params: { file },
  });

  createAxiosResponseInterceptor(axiosInstance);

  const fetcher = createAxiosFetcher(
    // Bridge axios' dual ESM/CJS declaration mismatch in axios@1.13.x.
    axiosInstance as unknown as Parameters<typeof createAxiosFetcher>[0],
  );

  const Provider = H5GroveProvider({
    url: `${process.env.EUPHROSYNE_TOOLS_API_URL}/hdf5`,
    filepath: file || "",
    fetcher,
    children: h5webApp,
  });

  return token ? Provider : <></>;
}
