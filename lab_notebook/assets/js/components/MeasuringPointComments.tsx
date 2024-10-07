import { css } from "@emotion/react";
import { updateMeasuringPointComments } from "../../../../lab/assets/js/measuring-point.services";
import { useContext } from "react";
import { NotebookContext } from "../Notebook.context";
import debounce from "lodash.debounce";

const textAreaStyle = css({
  width: "100%",
});
export default function MeasuringPointComments({
  pointId,
  value,
}: {
  pointId: string;
  value: string | null;
}) {
  const t = {
    comments: window.gettext("Comments"),
  };
  const textareaId = `point-${pointId}-textarea`;

  const { runId } = useContext(NotebookContext);

  const onCommentsChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateMeasuringPointComments(runId, pointId, event.target.value);
  };
  const debouncedOnCommentsChange = debounce(onCommentsChange, 400);

  return (
    <div className="fr-input-group">
      <label className="fr-label" htmlFor={textareaId}>
        {t.comments}
      </label>
      <textarea
        className="fr-input"
        id={textareaId}
        rows={12}
        css={textAreaStyle}
        defaultValue={value || ""}
        onChange={debouncedOnCommentsChange}
      ></textarea>
    </div>
  );
}
