export default function UpcomingProjectNoDataCard() {
  return (
    <div className="fr-card fr-card--shadow fr-card--horizontal">
      <div className="fr-card__body">
        <div className="fr-card__content">
          <h3 className="fr-card__title"></h3>
          <p className="fr-card__desc">
            <span className="fr-icon-goblet-line" aria-hidden="true"></span>
            <br className="fr-mb-1w" />
            {window.gettext("No upcoming projects")}
          </p>
          <div className="fr-card__start"></div>
          <div className="fr-card__end">
            <p className="fr-card__detail"></p>
          </div>
        </div>
      </div>
    </div>
  );
}
