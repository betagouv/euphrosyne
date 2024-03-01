export function getTemplateJSONData<Type>(elementId: string): Type | null {
  const element = document.querySelector<HTMLScriptElement>(`#${elementId}`);
  if (!element || !element.text) {
    return null;
  }
  return JSON.parse(element.text);
}
