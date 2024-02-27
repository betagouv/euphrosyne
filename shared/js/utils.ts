export function getTemplateJSONData<Type>(elementId: string): Type | null {
  const element = document.querySelector<HTMLScriptElement>(`#${elementId}`);
  if (!element || !element.text) {
    return null;
  }
  try {
    return JSON.parse(element.text);
  } catch (e) {
    return null;
  }
}
