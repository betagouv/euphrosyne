import { jwtFetch } from "../../../assets/js/jwt.js";

async function fetchVMConnectionLink(projectSlug) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/connect/${projectSlug}`,
    {
      method: "GET",
    }
  );
  if (response.ok) {
    return (await response.json())["url"];
  } else if (response.status === 404) {
    return null;
  }
  throw new Error(`An error occured while fetching project ${projectSlug} VM`);
}

async function fetchDeploymentStatus(projectSlug) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/deployments/${projectSlug}`,
    {
      method: "GET",
    }
  );
  if (response.ok) {
    return (await response.json())["status"];
  } else if (response.status === 404) {
    return null;
  }
  throw new Error(
    `An error occured while fetching project ${projectSlug} deployment status`
  );
}

function deployVM(projectSlug) {
  return jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/deployments/${projectSlug}`,
    {
      method: "POST",
    }
  );
}

function deleteVM(projectSlug) {
  return jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/vms/${projectSlug}`,
    {
      method: "DELETE",
    }
  );
}

async function fetchProjectVmSize(projectSlug) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/config/${projectSlug}/vm-size`,
    {
      method: "GET",
    }
  );
  if (response.ok) {
    return (await response.json())["vm_size"];
  }
}

async function setProjectVmSize(projectSlug, vmSize) {
  return jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/config/${projectSlug}/vm-size`,
    {
      method: "POST",
      body: JSON.stringify({ vm_size: vmSize }),
    }
  );
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
