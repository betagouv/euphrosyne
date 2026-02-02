import { useCallback, useEffect, useRef, useState } from "react";
import type { Participation } from "../types";
import ParticipationTable from "./ParticipationTable";
import {
  deleteParticipation,
  fetchLeaderParticipation,
  fetchParticipations,
} from "../participation.service";
import ParticipationFormModal from "./ParticipationFormModal";
import { UserData } from "../../../../../euphrosyne/assets/js/main";

interface ProjectParticipationsFormProps {
  projectId: number;
  userData: UserData;
  isRadiationProtectionEnabled: boolean;
  employerFormExemptRorIds: string[];
}

interface AddParticipationButtonProps {
  modalId: string;
  ref?: React.RefObject<HTMLButtonElement | null>;
  title?: string;
  onClick?: () => void;
}

function isLabAdminOrProjectLeader(
  userData: UserData,
  leaderParticipation: Participation | null,
) {
  return !!(
    userData.isLabAdmin ||
    (leaderParticipation && userData.email === leaderParticipation.user.email)
  );
}

function NoData({
  sectionTitle,
  message,
}: {
  message: string;
  sectionTitle: string;
}) {
  return (
    <div>
      <h4>{sectionTitle}</h4>
      <p>{message}</p>
    </div>
  );
}

function AddParticipationButton({
  modalId,
  ref,
  title,
  onClick,
}: AddParticipationButtonProps) {
  const t = {
    addMember: window.gettext("Add member"),
  };

  const _onClick = () => {
    const modalElement = document.getElementById(modalId);

    // @ts-expect-error: Property 'dsfr' does not exist on type 'Window & typeof globalThis'.ts(2339)
    window.dsfr(modalElement).modal.disclose();
    onClick?.();
  };

  return (
    <div style={{ display: "flex", justifyContent: "flex-end" }}>
      <button
        ref={ref}
        className="fr-btn fr-icon-add-line fr-btn--icon-left fr-btn--secondary"
        aria-controls={modalId}
        onClick={_onClick}
        type="button"
      >
        {title || t.addMember}
      </button>
    </div>
  );
}

export default function ProjectParticipationsForm({
  projectId,
  userData,
  isRadiationProtectionEnabled,
  employerFormExemptRorIds,
}: ProjectParticipationsFormProps) {
  const t = {
    leaderParticipationsTable: window.gettext("Project leader"),
    remoteParticipationsTable: window.gettext("Remote participations"),
    onPremisesParticipationsTable: window.gettext("On-site participations"),
    addLeaderButtonTitle: window.gettext("Add project leader"),
    leaderModalTitle: window.gettext("Project leader"),
    remoteNoData: window.gettext("No remote participations for this project."),
    onPremisesNoData: window.gettext(
      "No on-site participations for this project.",
    ),
    leaderNoData: window.gettext("No project leader assigned."),
  };

  const leaderModalId = "modal-leader-participation";
  const remoteModalId = "modal-remote-participation";
  const onPremisesModalId = "modal-onpremises-participation";

  const [leaderParticipation, setLeaderParticipation] =
    useState<Participation | null>(null);
  const [remoteParticipations, setRemoteParticipations] = useState<
    Participation[]
  >([]);
  const [onPremisesParticipations, setOnPremisesParticipations] = useState<
    Participation[]
  >([]);

  const leaderModalButton = useRef<HTMLButtonElement>(null);
  const remoteModalButton = useRef<HTMLButtonElement>(null);
  const onPremisesModalButton = useRef<HTMLButtonElement>(null);

  const [remoteParticipationToEdit, setRemoteParticipationToEdit] =
    useState<Participation | null>(null);
  const [onPremisesParticipationToEdit, setOnPremisesParticipationToEdit] =
    useState<Participation | null>(null);

  const loadParticipations = useCallback(async () => {
    await fetchLeaderParticipation(projectId).then((data) => {
      setLeaderParticipation(data);
    });
    await fetchParticipations(projectId, "remote").then((data) => {
      setRemoteParticipations(data);
    });
    await fetchParticipations(projectId, "on-premises").then((data) => {
      setOnPremisesParticipations(data);
    });
  }, [projectId]);

  const onDeleteClick = useCallback(
    async (participation: Participation) => {
      await deleteParticipation(projectId, participation.id);
      loadParticipations();
    },
    [projectId, loadParticipations],
  );

  useEffect(() => {
    loadParticipations();
  }, [loadParticipations]);

  return (
    <div className="fr-mb-5w">
      <ParticipationFormModal
        modalId={leaderModalId}
        participationType="leader"
        participation={leaderParticipation}
        projectId={projectId}
        employerFormExemptRorIds={employerFormExemptRorIds}
        onFormSubmit={() => loadParticipations()}
        modalTitle={t.leaderModalTitle}
      />
      <ParticipationFormModal
        modalId={remoteModalId}
        participationType="remote"
        participation={remoteParticipationToEdit}
        projectId={projectId}
        employerFormExemptRorIds={employerFormExemptRorIds}
        onFormSubmit={() => loadParticipations()}
      />
      <ParticipationFormModal
        modalId={onPremisesModalId}
        participationType="on-premises"
        participation={onPremisesParticipationToEdit}
        projectId={projectId}
        employerFormExemptRorIds={employerFormExemptRorIds}
        onFormSubmit={() => loadParticipations()}
      />

      <div>
        {leaderParticipation === null ? (
          <NoData
            sectionTitle={t.leaderParticipationsTable}
            message={t.leaderNoData}
          />
        ) : (
          <ParticipationTable
            participations={[leaderParticipation].filter(
              (p): p is Participation => p !== null,
            )}
            tableCaption={t.leaderParticipationsTable}
            editModalId={leaderModalId}
            canDelete={false}
            canEdit={userData.isLabAdmin}
            isRadiationProtectionEnabled={isRadiationProtectionEnabled}
          />
        )}
        {!leaderParticipation && userData.isLabAdmin && (
          <AddParticipationButton
            modalId={leaderModalId}
            ref={leaderModalButton}
            title={t.addLeaderButtonTitle}
          />
        )}
      </div>

      <div>
        {onPremisesParticipations.length === 0 ? (
          <NoData
            sectionTitle={t.onPremisesParticipationsTable}
            message={t.onPremisesNoData}
          />
        ) : (
          <ParticipationTable
            participations={onPremisesParticipations}
            tableCaption={t.onPremisesParticipationsTable}
            editModalId={onPremisesModalId}
            canDelete={isLabAdminOrProjectLeader(userData, leaderParticipation)}
            canEdit={isLabAdminOrProjectLeader(userData, leaderParticipation)}
            onDeleteClick={onDeleteClick}
            onEditClick={(participation) => {
              setOnPremisesParticipationToEdit(participation);
            }}
            isRadiationProtectionEnabled={isRadiationProtectionEnabled}
          />
        )}
        {isLabAdminOrProjectLeader(userData, leaderParticipation) && (
          <AddParticipationButton
            modalId={onPremisesModalId}
            onClick={() => {
              setOnPremisesParticipationToEdit(null);
            }}
            ref={onPremisesModalButton}
          />
        )}
      </div>

      <div>
        {remoteParticipations.length === 0 ? (
          <NoData
            sectionTitle={t.remoteParticipationsTable}
            message={t.remoteNoData}
          />
        ) : (
          <ParticipationTable
            participations={remoteParticipations}
            tableCaption={t.remoteParticipationsTable}
            editModalId={remoteModalId}
            onDeleteClick={onDeleteClick}
            canDelete={isLabAdminOrProjectLeader(userData, leaderParticipation)}
            canEdit={isLabAdminOrProjectLeader(userData, leaderParticipation)}
            onEditClick={(participation) => {
              setRemoteParticipationToEdit(participation);
            }}
          />
        )}
        {isLabAdminOrProjectLeader(userData, leaderParticipation) && (
          <AddParticipationButton
            modalId={remoteModalId}
            onClick={() => {
              setRemoteParticipationToEdit(null);
            }}
            ref={remoteModalButton}
          />
        )}
      </div>
    </div>
  );
}
