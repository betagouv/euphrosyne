import { jwtFetch } from "../../../../shared/js/jwt.js";

async function fetchVMConnectionLink(projectSlug, fetchFn = jwtFetch) {
  const response = await fetchFn(`/connect/${projectSlug}`, {
    method: "GET",
  });
  if (response.ok) {
    return (await response.json())["url"];
  } else if (response.status === 404) {
    return null;
  }
  throw new Error(`An error occured while fetching project ${projectSlug} VM`);
}

async function fetchDeploymentStatus(projectSlug, fetchFn = jwtFetch) {
  const response = await fetchFn(`/deployments/${projectSlug}`, {
    method: "GET",
  });
  if (response.ok) {
    return (await response.json())["status"];
  } else if (response.status === 404) {
    return null;
  }
  throw new Error(
    `An error occured while fetching project ${projectSlug} deployment status`,
  );
}

function deployVM(projectSlug, fetchFn = jwtFetch) {
  return fetchFn(`/deployments/${projectSlug}`, {
    method: "POST",
  });
}

function deleteVM(projectSlug, fetchFn = jwtFetch) {
  return fetchFn(`/vms/${projectSlug}`, {
    method: "DELETE",
  });
}

async function fetchProjectVmSize(projectSlug, fetchFn = jwtFetch) {
  const response = await fetchFn(`/config/${projectSlug}/vm-size`, {
    method: "GET",
  });
  if (response.ok) {
    return (await response.json())["vm_size"];
  }
}

async function setProjectVmSize(projectSlug, vmSize, fetchFn = jwtFetch) {
  return fetchFn(`/config/${projectSlug}/vm-size`, {
    method: "POST",
    body: JSON.stringify({ vm_size: vmSize }),
  });
}

const exports = {
  fetchVMConnectionLink,
  fetchDeploymentStatus,
  deployVM,
  deleteVM,
  fetchProjectVmSize,
  setProjectVmSize,
};
export default exports;
