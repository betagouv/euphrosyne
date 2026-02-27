export default function ExtensionTags({
  files,
  selectedExtensions,
  onExtensionClick,
}: {
  files: string[];
  selectedExtensions: string[];
  onExtensionClick: (extension: string) => void;
}) {
  const getFileExtension = (file: string): string | null => {
    const fileName = file.split("/").pop() || file;
    const lastDotIndex = fileName.lastIndexOf(".");

    // Only treat trailing segments after a non-leading dot as extensions.
    if (lastDotIndex <= 0 || lastDotIndex === fileName.length - 1) {
      return null;
    }

    return fileName.slice(lastDotIndex + 1);
  };

  const extensions = [
    ...new Set(
      files
        .map((file) => getFileExtension(file))
        .filter((extension): extension is string => extension !== null),
    ),
  ];
  return (
    <ul className="fr-tags-group">
      {extensions.map((extension) => (
        <li key={extension}>
          <button
            type="button"
            className="fr-tag"
            aria-pressed={selectedExtensions.includes(extension)}
            onClick={() => onExtensionClick(extension)}
          >
            .{extension}
          </button>
        </li>
      ))}
    </ul>
  );
}
