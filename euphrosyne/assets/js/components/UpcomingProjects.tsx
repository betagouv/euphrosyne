import { useState, useEffect } from "react";
import UpcomingProjectCard from "./UpcomingProjectCard";
import PlaceholderCard from "./PlaceholderCard";
import { UpcomingProject } from "../IProject";
import { css } from "@emotion/react";

interface UpcomingProjectsResponseElement {
  name: string;
  start_date: string;
  change_url: string;
  status: {
    label: string;
    class_name: string;
  };
  num_runs: number;
}

async function fetchUpcomingProjects(): Promise<UpcomingProject[]> {
  const projects = (await (
    await fetch("/api/lab/projects/upcoming")
  ).json()) as UpcomingProjectsResponseElement[];
  return projects.map((p) => ({
    name: p.name,
    startDate: p.start_date,
    changeUrl: p.change_url,
    status: {
      label: p.status.label,
      className: p.status.class_name,
    },
    runCount: p.num_runs,
  }));
}

export default function UpcomingProjects(): JSX.Element {
  const [upcomingProjects, setUpcomingProjects] = useState<UpcomingProject[]>(
    []
  );
  useEffect(() => {
    fetchUpcomingProjects().then(setUpcomingProjects);
  }, []);

  return (
    <div className="fr-container--fluid">
      <div
        className="fr-grid-row fr-grid-row--gutters"
        css={css`
          min-height: 226px;
        `}
      >
        {upcomingProjects.length ? (
          upcomingProjects.map((project) => (
            <div
              key={`upcoming-project-${project.name}`}
              className="fr-col-6 fr-col-sm-3"
            >
              <UpcomingProjectCard project={project} />
            </div>
          ))
        ) : (
          <div className="fr-col-6 fr-col-sm-3">
            <PlaceholderCard />{" "}
          </div>
        )}
      </div>
    </div>
  );
}
