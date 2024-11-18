import { jwtFetch } from "../../../../shared/js/jwt";

interface ListImageDefinitionsResponse {
  image_definitions: string[];
}

export async function fetchImageDefinitions(
  fetchFn: typeof jwtFetch = jwtFetch,
) {
  const response = await fetchFn(`/vms/image-definitions`);
  if (response?.ok) {
    const data = (await response.json()) as ListImageDefinitionsResponse;
    return data.image_definitions;
  }
  return [];
}

export async function fetchProjectImageDefinition(
  projectSlug: string,
  fetchFn: typeof jwtFetch = jwtFetch,
) {
  const response = await fetchFn(`/config/${projectSlug}/image-definition`);
  if (response?.ok) {
    const data = await response.json();
    return data.image_definition;
  } else {
    throw new Error("Failed to fetch project image definition");
  }
}

export async function setProjectImageDefinition(
  projectSlug: string,
  imageDefinition: string,
  fetchFn: typeof jwtFetch = jwtFetch,
) {
  const response = await fetchFn(`/config/${projectSlug}/image-definition`, {
    method: "POST",
    body: JSON.stringify(imageDefinition),
  });
  if (!response?.ok) {
    throw new Error("Failed to set project image definition");
  }
}
