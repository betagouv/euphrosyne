import * as React from "react";

interface ObjectGroupMaterialsCellProps {
  materials: string[];
}
export default function ObjectGroupMaterialsCell({
  materials,
}: ObjectGroupMaterialsCellProps) {
  const materialsToDisplay = materials.slice(0, 3);
  return (
    <>
      {materialsToDisplay.map((material) => (
        <React.Fragment key={`material-cell-${material}`}>
          <p
            className="fr-tag fr-tag--sm"
            key={`material-${material}`}
            aria-describedby={`tooltip-material-${material}`}
          >
            {material.substring(0, 8)}
            {material.length > 8 && "..."}
          </p>
          <span
            className="fr-tooltip fr-placement"
            id={`tooltip-material-${material}`}
            role="tooltip"
            aria-hidden="true"
          >
            {material}
          </span>
        </React.Fragment>
      ))}
      {materials.length > 3 && (
        <p className="fr-tag fr-tag--sm">+{materials.length - 3}</p>
      )}
    </>
  );
}
