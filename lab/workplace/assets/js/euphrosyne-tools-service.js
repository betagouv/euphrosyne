import { jwtFetch } from "../../../assets/js/jwt.js";

async function fetchVMConnectionLink(projectName) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/connect/${projectName}`,
    {
      method: "GET",
    }
  );
  if (response.ok) {
    return (await response.json())["url"];
  } else if (response.status === 404) {
    return null;
  }
  throw new Error(`An error occured while fetching project ${projectName} VM`);
}

async function fetchDeploymentStatus(projectName) {
  const response = await jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/deployments/${projectName}`,
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
    `An error occured while fetching project ${projectName} deployment status`
  );
}

function deployVM(projectName) {
  return jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/deployments/${projectName}`,
    {
      method: "POST",
    }
  );
}

function deleteVM(projectName) {
  return jwtFetch(
    `${process.env.EUPHROSYNE_TOOLS_API_URL}/vms/${projectName}`,
    {
      method: "DELETE",
    }
  );
}

const exports = {
  fetchVMConnectionLink,
  fetchDeploymentStatus,
  deployVM,
  deleteVM,
};
export default exports;
