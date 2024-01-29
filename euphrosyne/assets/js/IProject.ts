export interface ProjectStatus {
  label: string;
  className: string;
}

export interface Project {
  name: string;
  leader: string;
  status: ProjectStatus;
}
