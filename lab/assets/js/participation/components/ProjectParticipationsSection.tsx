import { useCallback, useEffect, useRef, useState } from "react";
import type { Participation } from "../types";
import ParticipationTable from "./ParticipationTable";
import {
  deleteParticipation,
  fetchParticipations,
} from "../participation.service";
import ParticipationFormModal from "./ParticipationFormModal";

interface ProjectParticipationsFormProps {
  projectId: number;
}

interface AddParticipationButtonProps {
  modalId: string;
  ref?: React.RefObject<HTMLButtonElement | null>;
  onClick?: () => void;
}

function AddParticipationButton({
  modalId,
  ref,
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
        {t.addMember}
      </button>
    </div>
  );
}

export default function ProjectParticipationsForm({
  projectId,
}: ProjectParticipationsFormProps) {
  const t = {
    remoteParticipationsTable: window.gettext("Remote participations"),
    onPremisesParticipationsTable: window.gettext("On-site participations"),
  };

  const remoteModalId = "modal-remote-participation";
  const onPremisesModalId = "modal-onpremises-participation";

  const [remoteParticipations, setRemoteParticipations] = useState<
    Participation[]
  >([]);
  const [onPremisesParticipations, setOnPremisesParticipations] = useState<
    Participation[]
  >([]);

  const remoteModalButton = useRef<HTMLButtonElement>(null);
  const onPremisesModalButton = useRef<HTMLButtonElement>(null);

  const [remoteParticipationToEdit, setRemoteParticipationToEdit] =
    useState<Participation | null>(null);
  const [onPremisesParticipationToEdit, setOnPremisesParticipationToEdit] =
    useState<Participation | null>(null);

  const loadParticipations = useCallback(async () => {
    const remoteData = await fetchParticipations(projectId, "remote");
    setRemoteParticipations(remoteData);
    const onPremisesData = await fetchParticipations(projectId, "on-premises");
    setOnPremisesParticipations(onPremisesData);
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
        modalId={remoteModalId}
        participationType="remote"
        participation={remoteParticipationToEdit}
        projectId={projectId}
        onFormSubmit={() => loadParticipations()}
      />
      <ParticipationFormModal
        modalId={onPremisesModalId}
        participationType="on-premises"
        participation={onPremisesParticipationToEdit}
        projectId={projectId}
        onFormSubmit={() => loadParticipations()}
      />

      <div>
        <ParticipationTable
          participations={onPremisesParticipations}
          tableCaption={t.onPremisesParticipationsTable}
          editModalId={onPremisesModalId}
          onDeleteClick={onDeleteClick}
          onEditClick={(participation) => {
            setOnPremisesParticipationToEdit(participation);
          }}
        />
        <AddParticipationButton
          modalId={onPremisesModalId}
          onClick={() => {
            setOnPremisesParticipationToEdit(null);
          }}
          ref={onPremisesModalButton}
        />
      </div>

      <div>
        <ParticipationTable
          participations={remoteParticipations}
          tableCaption={t.remoteParticipationsTable}
          onDeleteClick={onDeleteClick}
          onEditClick={(participation) => {
            setRemoteParticipationToEdit(participation);
            remoteModalButton.current?.click();
          }}
        />
        <AddParticipationButton
          modalId={remoteModalId}
          onClick={() => {
            setRemoteParticipationToEdit(null);
          }}
          ref={remoteModalButton}
        />
      </div>
    </div>
  );
}
