import { css } from "@emotion/react";

const textAreaStyle = css({
  width: "100%",
});
export default function MeasuringPointComments({
  pointId,
}: {
  pointId: string;
}) {
  const t = {
    comments: window.gettext("Comments"),
  };
  const textareaId = `point-${pointId}-textarea`;
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
      ></textarea>
    </div>
  );
}
