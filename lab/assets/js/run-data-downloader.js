import { jwtFetch } from "../../../shared/js/jwt.js";

export default async function downloadRunData(
  projectSlug,
  runName,
  runDataType,
  fetchFn = jwtFetch,
) {
  const path = `projects/${projectSlug}/runs/${runName}/${runDataType}`;
  const response = await fetchFn(`/data/${projectSlug}/token?path=${path}`, {
    method: "GET",
  });
  const { token } = await response.json();
  if (!token) {
    throw new Error("Failed to get token to download run data.");
  }
  window.open(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/data/run-data-zip?path=${path}&token=${token}`,
    "_blank",
  );
}
