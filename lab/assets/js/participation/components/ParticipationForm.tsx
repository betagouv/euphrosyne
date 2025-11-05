import { useEffect, useState } from "react";
import {
  Employer,
  Institution,
  Participation,
  ParticipationType,
} from "../types";
import InstitutionAutocomplete from "./InstitutionAutocomplete";
import {
  addParticipation,
  editParticipation,
  ParticipationAddData,
  ParticipationValidationError,
  setProjectLeader,
  ValidationDataError,
} from "../participation.service";
import FieldError from "./FieldError";
import { useFormStatus } from "react-dom";

interface ParticipationFormProps {
  projectId: number;
  participationType: ParticipationType;
  participation?: Participation | null;
  onSuccess?: () => void;
}

function SubmitButton() {
  const t = {
    submit: window.gettext("Save member information"),
  };
  const { pending } = useFormStatus();
  return (
    <button className="fr-btn" type="submit" disabled={pending}>
      {t.submit}
    </button>
  );
}

export default function ParticipationForm({
  projectId,
  participation,
  participationType,
  onSuccess,
}: ParticipationFormProps) {
  const t = {
    userFieldsetLegend: window.gettext("Researcher information"),
    email: window.gettext("Email"),
    firstName: window.gettext("First name"),
    lastName: window.gettext("Last name"),
    institution: window.gettext("Institution"),
    country: window.gettext("Country"),
    employerFieldsetLegend: window.gettext("Employer information"),
    function: window.gettext("Function"),
    submit: window.gettext("Save member information"),
    associatedRor: window.gettext("Associated ROR page"),
    disabledReason: window.gettext(
      "Email cannot be edited after creation. Delete this participation and invite a new member.",
    ),
  };

  const [email, setEmail] = useState("");
  const [participationId, setParticipationId] = useState<number | null>(null);

  const [institution, setInstitution] = useState<Institution>({
    name: "",
    id: null,
    country: "",
    rorId: null,
  });

  const [employer, setEmployer] = useState<Employer>({
    firstName: "",
    lastName: "",
    email: "",
    function: "",
  });

  const [errors, setErrors] =
    useState<ValidationDataError<ParticipationAddData> | null>(null);

  const resetForm = () => {
    setEmail("");
    setInstitution({
      name: "",
      id: null,
      country: "",
      rorId: null,
    });
    setEmployer({
      firstName: "",
      lastName: "",
      email: "",
      function: "",
    });
    setErrors(null);
  };

  const onSubmit = async () => {
    if (!institution.country) {
      return;
    }
    try {
      if (participationType === "leader") {
        await setProjectLeader(
          projectId,
          {
            user: { email },
            institution: {
              name: institution.name,
              country: institution.country,
              rorId: institution.rorId,
            },
            employer,
          },
          !!participationId,
        );
        setErrors(null);
        onSuccess?.();
        return;
      }
      if (participationId) {
        await editParticipation(projectId, participationType, participationId, {
          institution: {
            name: institution.name,
            country: institution.country,
            rorId: institution.rorId,
          },
          employer: participationType === "remote" ? undefined : employer,
        });
      } else {
        await addParticipation(projectId, participationType, {
          ...participation,
          user: {
            email,
          },
          institution: {
            name: institution.name,
            country: institution.country,
            rorId: institution.rorId,
          },
          employer: participationType === "remote" ? null : employer,
        });
      }

      resetForm();
      onSuccess?.();
    } catch (error) {
      if (error instanceof ParticipationValidationError) {
        setErrors(error.fieldErrors);
      }
    }
  };

  useEffect(() => {
    setParticipationId(participation?.id || null);
    setEmail(participation?.user.email || "");
    setInstitution(
      participation?.institution || {
        name: "",
        id: null,
        country: "",
        rorId: null,
      },
    );
    setEmployer({
      firstName: participation?.employer?.firstName || "",
      lastName: participation?.employer?.lastName || "",
      email: participation?.employer?.email || "",
      function: participation?.employer?.function || "",
    });
  }, [participation]);

  return (
    <form action={onSubmit}>
      <fieldset
        className={`fr-fieldset ${errors && (errors.user || errors.institution) ? "fr-fieldset--error" : ""}`}
        aria-labelledby="participation-user-messages participation-institution-messages"
      >
        <legend className="fr-fieldset__legend" id="researcher-legend">
          {t.userFieldsetLegend}
        </legend>
        <div className="fr-fieldset__element">
          <div className="fr-input-group">
            <label className="fr-label" htmlFor="participation-email">
              {t.email}
              {participationType !== "leader" && !!participationId && (
                <span className="fr-hint-text">{t.disabledReason}</span>
              )}
            </label>
            <input
              className="fr-input"
              id="participation-user-email"
              type="email"
              aria-describedby="participation-user-email-messages"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required={!participationId}
              autoComplete="on"
              disabled={participationType !== "leader" && !!participationId}
            />
            <FieldError errors={errors} firstKey="user" secondKey="email" />
            <FieldError errors={errors} firstKey="user" />
          </div>
        </div>
        <div className="fr-fieldset__element">
          <div className="fr-input-group">
            <label
              className="fr-label"
              htmlFor="participation-institution-name"
            >
              {t.institution}
              {institution?.rorId && (
                <span className="fr-hint-text">
                  {t.associatedRor}:&nbsp;
                  <a href={institution.rorId}>{institution.rorId}</a>
                </span>
              )}
            </label>
            <InstitutionAutocomplete
              name="institution"
              value={institution}
              onChange={(i) => i && setInstitution(i)}
              id="participation-institution-name"
              className="fr-mt-2v"
            />
            <FieldError
              errors={errors}
              firstKey="institution"
              secondKey="name"
            />
          </div>
        </div>
        <FieldError errors={errors} firstKey="institution" />
      </fieldset>

      {participationType !== "remote" && (
        <fieldset
          className={`fr-fieldset ${errors && errors.employer ? "fr-fieldset--error" : ""}`}
          aria-labelledby="participation-employer-messages"
        >
          <legend className="fr-fieldset__legend" id="employer-text-legend">
            {t.employerFieldsetLegend}
          </legend>
          <div className="fr-fieldset__element">
            <div className="fr-input-group">
              <label
                className="fr-label"
                htmlFor="participation-employer-email"
              >
                {t.email}
              </label>
              <input
                className="fr-input"
                id="participation-employer-email"
                type="text"
                value={employer.email}
                onChange={(e) =>
                  setEmployer({ ...employer, email: e.target.value })
                }
                aria-describedby="participation-employer-email-messages"
                required
              />
              <FieldError
                errors={errors}
                firstKey="employer"
                secondKey="email"
              />
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-input-group">
              <label
                className="fr-label"
                htmlFor="participation-employer-first_name"
              >
                {t.firstName}
              </label>
              <input
                className="fr-input"
                id="participation-employer-first_name"
                aria-describedby="participation-employer-first_name-messages"
                type="text"
                value={employer.firstName}
                onChange={(e) =>
                  setEmployer({ ...employer, firstName: e.target.value })
                }
                required
              />
              <FieldError
                errors={errors}
                firstKey="employer"
                secondKey="first_name"
              />
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-input-group">
              <label
                className="fr-label"
                htmlFor="participation-employer-last_name"
              >
                {t.lastName}
              </label>
              <input
                className="fr-input"
                id="participation-employer-last_name"
                aria-describedby="participation-employer-last_name-messages"
                type="text"
                value={employer.lastName}
                onChange={(e) =>
                  setEmployer({ ...employer, lastName: e.target.value })
                }
                required
              />
              <FieldError
                errors={errors}
                firstKey="employer"
                secondKey="last_name"
              />
            </div>
          </div>
          <div className="fr-fieldset__element">
            <div className="fr-input-group">
              <label
                className="fr-label"
                htmlFor="participation-employer-function"
              >
                {t.function}
              </label>
              <input
                className="fr-input"
                id="participation-employer-function"
                type="text"
                value={employer.function}
                onChange={(e) =>
                  setEmployer({ ...employer, function: e.target.value })
                }
                required
              />
              <FieldError
                errors={errors}
                firstKey="employer"
                secondKey="function"
              />
            </div>
          </div>
          <FieldError errors={errors} firstKey="employer" />
        </fieldset>
      )}

      <SubmitButton />
    </form>
  );
}
