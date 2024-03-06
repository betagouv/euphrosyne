import { useState, useEffect } from "react";
import { css } from "@emotion/react";

import { UpcomingProject } from "../IProject";

import UpcomingProjectCard from "./UpcomingProjectCard";
import PlaceholderCard from "./PlaceholderCard";
import UpcomingProjectNoDataCard from "./UpcomingProjectNoDataCard";

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
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    fetchUpcomingProjects().then((projects) => {
      setUpcomingProjects(projects);
      setIsLoading(false);
    });
  }, []);

  return (
    <div className="fr-container--fluid">
      <div
        className="fr-grid-row fr-grid-row--gutters"
        css={css`
          min-height: 226px;
        `}
      >
        {isLoading ? (
          <div className="fr-col-6 fr-col-sm-4 fr-col-md-3">
            <PlaceholderCard />{" "}
          </div>
        ) : (
          <>
            {upcomingProjects.length ? (
              upcomingProjects.map((project) => (
                <div
                  key={`upcoming-project-${project.name}`}
                  className="fr-col-6 fr-col-sm-4 fr-col-lg-3"
                >
                  <UpcomingProjectCard project={project} />
                </div>
              ))
            ) : (
              <div className="fr-col-6 fr-col-sm-4 fr-col-md-3">
                <UpcomingProjectNoDataCard />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
