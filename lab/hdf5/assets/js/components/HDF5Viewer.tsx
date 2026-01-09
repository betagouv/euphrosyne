import { App, H5GroveProvider } from "@h5web/app";
import { getToken } from "../../../../../shared/js/jwt";
import { useEffect, useState } from "react";
import { Axios } from "axios";

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
          // Retry the initial call, but with the updated token in the headers.
          // Resolves the promise if successful
          return new Axios(error.response.config);
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

  const Provider = H5GroveProvider({
    url: `${process.env.EUPHROSYNE_TOOLS_API_URL}/hdf5`,
    filepath: file || "",
    axiosConfig: {
      params: { file },
      headers: { Authorization: `Bearer ${token}` },
    },
    children: h5webApp,
  });
  createAxiosResponseInterceptor(Provider.props.api.client);

  return token ? Provider : <></>;
}
