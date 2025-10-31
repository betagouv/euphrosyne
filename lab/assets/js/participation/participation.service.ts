import { getCSRFToken } from "../utils";
import { Participation, ParticipationType } from "./types";

interface ParticipationResponse {
  id: number;
  on_premises: boolean;
  user: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
  };
  institution: {
    id: number;
    name: string;
    ror_id: string;
    country: string;
  } | null;
  employer: {
    first_name: string;
    last_name: string;
    email: string;
    function: string;
  } | null;
}

export interface ParticipationAddData {
  user: {
    email: string;
  };
  institution: {
    name: string;
    country: string;
    rorId: string | null;
  };
  employer: {
    firstName: string;
    lastName: string;
    email: string;
    function: string;
  } | null;
}

interface ParticipationEditData {
  institution?: {
    name: string;
    country: string;
    rorId: string | null;
  };
  employer?: {
    firstName: string;
    lastName: string;
    email: string;
    function: string;
  };
}

export type ValidationDataError<T> = {
  [K in keyof T]?:
    | (string[] | { non_field_errors: string[] })
    | ValidationDataError<T[K]>;
};

export type BadRequestErrorData = Record<
  string,
  Record<string, string[]> | string[]
>;

export class ParticipationValidationError<T> extends Error {
  constructor(
    message: string,
    public fieldErrors: ValidationDataError<T>,
  ) {
    super(message);
    this.name = "ParticipationValidationError";
    this.fieldErrors = fieldErrors;
  }
}

function convertDataToParticipation(
  data: ParticipationResponse,
): Participation {
  return {
    id: data.id,
    onPremises: data.on_premises,
    user: {
      id: data.user.id,
      firstName: data.user.first_name,
      lastName: data.user.last_name,
      email: data.user.email,
    },
    institution: data.institution
      ? {
          id: data.institution.id,
          name: data.institution.name,
          rorId: data.institution.ror_id,
          country: data.institution.country,
        }
      : null,
    employer: data.employer
      ? {
          firstName: data.employer.first_name,
          lastName: data.employer.last_name,
          email: data.employer.email,
          function: data.employer.function,
        }
      : null,
  };
}

export async function fetchParticipations(
  projectId: number,
  type: ParticipationType,
): Promise<Participation[]> {
  const response = await fetch(
    `/api/lab/projects/${projectId}/participations/${type}`,
  );
  if (!response.ok) {
    console.error(`Error fetching ${type} participations`);
    return [];
  }
  const data = (await response.json()) as ParticipationResponse[] | null;
  if (!data) {
    return [];
  }

  return data.map((item) => convertDataToParticipation(item));
}

export async function addParticipation(
  projectId: number,
  type: ParticipationType,
  participationData: ParticipationAddData,
): Promise<Participation> {
  const response = await fetch(
    `/api/lab/projects/${projectId}/participations/${type}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken() || "",
      },
      body: JSON.stringify({
        user: {
          email: participationData.user.email,
        },
        institution: {
          name: participationData.institution.name,
          country: participationData.institution.country,
          ror_id: participationData.institution.rorId,
        },
        employer: participationData.employer
          ? {
              first_name: participationData.employer.firstName,
              last_name: participationData.employer.lastName,
              email: participationData.employer.email,
              function: participationData.employer.function,
            }
          : null,
      }),
    },
  );
  if (response.status === 400) {
    const errorData = (await response.json()) as BadRequestErrorData;
    throw new ParticipationValidationError<ParticipationAddData>(
      `Validation error adding ${type} participation`,
      errorData,
    );
  }
  if (!response.ok) {
    throw new Error(`Error adding ${type} participation`);
  }
  const data = (await response.json()) as ParticipationResponse;

  return convertDataToParticipation(data);
}

export async function editParticipation(
  projectId: number,
  type: ParticipationType,
  participationId: number,
  participationData: ParticipationEditData,
): Promise<Participation> {
  const response = await fetch(
    `/api/lab/projects/${projectId}/participations/${participationId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken() || "",
      },
      body: JSON.stringify({
        institution: participationData?.institution
          ? {
              name: participationData?.institution?.name,
              country: participationData?.institution?.country,
              ror_id: participationData?.institution?.rorId,
            }
          : undefined,
        employer: participationData?.employer
          ? {
              first_name: participationData?.employer?.firstName,
              last_name: participationData?.employer?.lastName,
              email: participationData?.employer?.email,
              function: participationData?.employer?.function,
            }
          : undefined,
      }),
    },
  );
  if (response.status === 400) {
    const errorData = (await response.json()) as BadRequestErrorData;
    throw new ParticipationValidationError<ParticipationEditData>(
      `Validation error editing ${type} participation`,
      errorData,
    );
  }
  if (!response.ok) {
    throw new Error(`Error editing ${type} participation`);
  }
  const data = (await response.json()) as ParticipationResponse;

  return convertDataToParticipation(data);
}

export async function deleteParticipation(
  projectId: number,
  participationId: number,
): Promise<void> {
  const response = await fetch(
    `/api/lab/projects/${projectId}/participations/${participationId}`,
    {
      method: "DELETE",
      headers: {
        "X-CSRFToken": getCSRFToken() || "",
      },
    },
  );
  if (!response.ok) {
    throw new Error(`Error deleting participation ${participationId}`);
  }
}
