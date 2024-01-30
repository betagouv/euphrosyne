import { UpcomingProject } from "../IProject";

interface UpcomingProjectCardProps {
  project: UpcomingProject;
}

export default function UpcomingProjectCard({
  project,
}: UpcomingProjectCardProps): JSX.Element {
  return (
    <div className="fr-card fr-card--shadow fr-card--horizontal fr-card--sm">
      <div className="fr-card__body">
        <div className="fr-card__content">
          <h3 className="fr-card__title">
            <a href={project.changeUrl}>
              {project.name.length > 14
                ? `${project.name.substring(0, 14)}...`
                : project.name}
            </a>
          </h3>
          <p className="fr-card__desc">
            {new Date(project.startDate).toLocaleDateString()}
          </p>
          <div className="fr-card__start">
            <ul className="fr-tags-group">
              <li>
                <p className={`fr-tag ${project.status.className}`}>
                  {project.status.label}
                </p>
              </li>
            </ul>
          </div>
          <div className="fr-card__end">
            <p className="fr-card__detail">{project.runCount} runs</p>
          </div>
        </div>
      </div>
    </div>
  );
}
