export type ParticipationType = "on-premises" | "remote" | "leader";

export interface Employer {
  firstName: string;
  lastName: string;
  email: string;
  function: string;
}

export interface Institution {
  id: number | null;
  name: string;
  country: string | null;
  rorId: string | null;
}

export interface Participation {
  id: number;
  onPremises: boolean;
  user: {
    id: number;
    firstName: string;
    lastName: string;
    email: string;
  };
  institution: Institution | null;
  employer: Employer | null;
}
