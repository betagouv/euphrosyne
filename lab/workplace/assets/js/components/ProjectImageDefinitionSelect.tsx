import { useEffect, useState } from "react";

import {
  fetchImageDefinitions,
  fetchProjectImageDefinition,
  setProjectImageDefinition,
} from "../project-settings-service";

interface ProjectImageDefinitionSelectProps {
  projectSlug: string;
  fetchFn?: typeof fetch;
}

export default function ProjectImageDefinitionSelect({
  projectSlug,
  fetchFn,
}: ProjectImageDefinitionSelectProps) {
  const t = {
    "Image definition": window.gettext("Image definition"),
    Default: window.gettext("Default"),
    "Used to determine the image definition used to create the VM.":
      window.gettext(
        "Used to determine the image definition used to create the VM.",
      ),
    "An error ocurred while setting project image definition": window.gettext(
      "An error ocurred while setting project image definition",
    ),
  };

  const [imageDefinitions, setImageDefinitions] = useState<string[]>([]);
  const [imageDefinition, setImageDefinition] = useState<string>("");
  const [hasError, setHasError] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchImageDefinitions(fetchFn).then(setImageDefinitions);
    fetchProjectImageDefinition(projectSlug, fetchFn).then(setImageDefinition);
    setIsLoading(false);
  }, []);

  const onSelectionChange = async (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    if (hasError) setHasError(false);
    const { value } = event.target;
    setImageDefinition(value);
    try {
      await setProjectImageDefinition(projectSlug, value, fetchFn);
    } catch {
      setHasError(true);
    }
  };

  return (
    <div className={`fr-select-group ${hasError && "fr-select-group--error"}`}>
      <label htmlFor="vm-size-select">{t["Image definition"]}</label>
      <select
        name="image_definition"
        className={`fr-select ${hasError && "fr-select--error"}`}
        value={imageDefinition}
        onChange={onSelectionChange}
        aria-describedby={`${projectSlug}-image-definition-select--error`}
        disabled={isLoading}
      >
        <option value="">{t["Default"]}</option>
        {imageDefinitions.map((imageDefinition) => (
          <option key={imageDefinition} value={imageDefinition}>
            {imageDefinition}
          </option>
        ))}
      </select>
      {hasError && (
        <p
          id={`${projectSlug}-image-definition-select--error`}
          className="fr-error-text"
        >
          {t["An error ocurred while setting project image definition"]}
        </p>
      )}
      <div className="help">
        {t["Used to determine the image definition used to create the VM."]}
      </div>
    </div>
  );
}
