export async function parseRunningVMs(
  response: Response | undefined,
): Promise<string[]> {
  if (!response?.ok) {
    throw new Error(
      `Failed to list running VMs (status ${response?.status ?? "none"})`,
    );
  }
  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error("Unexpected running VMs response");
  }
  return data;
}
