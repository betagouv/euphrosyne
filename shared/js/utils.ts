export function getTemplateJSONData<Type>(elementId: string): Type | null {
  const element = document.querySelector<HTMLScriptElement>(`#${elementId}`);
  if (!element || !element.text) {
    return null;
  }
  const text = element.text.trim();
  if (text === "") {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (e) {
    console.error(
      `Error parsing JSON data for elementId: ${elementId}.\nContent: ${text}\nError: ${e}`,
    );
    return null;
  }
}
