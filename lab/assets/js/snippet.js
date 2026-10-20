export function loadFormsetRow(
  formsetPrefix,
  formIndex,
  objectId,
  objectName,
  objectChangeUrl,
  objectRepr,
  parentObjectName,
  parentObjectId,
) {
  const row = document.createElement("tr");
  row.className = `form-row has_original dynamic-${formsetPrefix}`;
  row.id = `${formsetPrefix}-${formIndex}`;

  const original = row.insertCell();
  original.className = "original";
  const description = document.createElement("p");
  description.textContent = `${formsetPrefix} object (${objectId})`;
  original.append(description);

  for (const [field, value] of [
    ["id", objectId],
    [parentObjectName, parentObjectId],
  ]) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = `${formsetPrefix}-${formIndex}-${field}`;
    input.id = `id_${input.name}`;
    input.value = value;
    original.append(input);
  }

  const object = row.insertCell();
  object.className = `field-${objectName}`;
  const paragraph = document.createElement("p");
  const link = document.createElement("a");
  link.href = objectChangeUrl;
  link.textContent = objectRepr;
  paragraph.append(link);
  object.append(paragraph);

  const deleteCell = row.insertCell();
  deleteCell.className = "delete";
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.name = `${formsetPrefix}-${formIndex}-DELETE`;
  checkbox.id = `id_${checkbox.name}`;
  deleteCell.append(checkbox);

  return row;
}
