import { ChangeEvent, HTMLProps, useContext, useId } from "react";
import { NotebookContext } from "../Notebook.context";

interface MeasuringPointStandardProps {
  standard: string | null;
  onStandardChange: (standard: string | null) => void;
}

export default function MeasuringPointStandard({
  standard,
  onStandardChange,
  ...props
}: MeasuringPointStandardProps & HTMLProps<HTMLDivElement>) {
  const t = {
    standardReference: window.gettext("Standard reference"),
    noStandard: window.gettext("No standard"),
  };
  const selectId = useId();

  const { standards } = useContext(NotebookContext);

  const changeStandard = async (event: ChangeEvent<HTMLSelectElement>) => {
    const standard = event.target.value;
    onStandardChange(standard === "" ? null : standard);
  };

  return (
    <div className={`fr-select-group ${props.className || ""}`} {...props}>
      <label className="fr-label" htmlFor={selectId}>
        {t.standardReference}
      </label>
      <select
        className="fr-select"
        id={selectId}
        name="select"
        onChange={changeStandard}
        value={standard || ""}
      >
        <option value="">{t.noStandard}</option>
        {standards.map((standard) => (
          <option
            key={`${selectId}-option-${standard.label}`}
            value={standard.label}
          >
            {standard.label}
          </option>
        ))}
      </select>
    </div>
  );
}
