export interface ProjectStatus {
  label: string;
  className: string;
}

export interface Project {
  name: string;
  leader: string;
  status: ProjectStatus;
}

export interface UpcomingProject {
  name: string;
  startDate: string;
  changeUrl: string;
  status: ProjectStatus;
  runCount: number;
}
