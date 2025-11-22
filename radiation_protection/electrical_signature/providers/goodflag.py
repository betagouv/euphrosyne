import enum
import logging
import mimetypes
import os
import typing
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

if typing.TYPE_CHECKING:
    from radiation_protection.models import ElectricalSignatureProcess


logger = logging.getLogger(__name__)

SIGNATURE_CONSENT_PAGE_ID = "cop_DK7inaJS6nLgUHng93CsQKaS"
# SIGNATURE_PROFILE_ID = "sip_JuK7JYy153CqAB83EUaAduC1"  # PDF
SIGNATURE_PROFILE_ID = "sip_JSwKQjyM1oRzTVVUEkG9bTKQ"  # WORD

REDIRECT_URL = f"{settings.SITE_URL}/electical_signature/webhooks/goodlfag"

SIGNATURE_EXPIRED_TD = timedelta(days=30)


class StepType(enum.StrEnum):
    APPROVAL = "approval"
    SIGNATURE = "signature"


class Recipient(typing.TypedDict):
    email: str
    first_name: str
    last_name: str
    preferred_locale: typing.NotRequired[str]


class Step(typing.TypedDict):
    step_type: StepType
    recipients: list[Recipient]


def start_workflow(workflow_name: str, steps: list[Step], document_path: str) -> str:
    client = GoodflagClient()

    workflow = client.create_workflow(
        name=workflow_name,
        steps=steps,
    )
    workflow_id = workflow["id"]

    doc_upload = client.upload_document(
        workflow_id,
        document_path,
    )

    for document in doc_upload["documents"]:
        client.create_viewer(
            document["id"],
        )

    client.start_workflow(workflow_id)
    return workflow_id


def get_status(signature_process: "ElectricalSignatureProcess") -> str | None:
    client = GoodflagClient()
    data = client.get_workflow_status(signature_process.provider_workflow_id)
    if data["workflowStatus"] == "started":
        steps_completed = "{}/{}".format(
            sum(1 for step in data["steps"] if step["isFinished"] is True),
            len(data["steps"]),
        )
        return _("started (%(steps_completed)s)") % {"steps_completed": steps_completed}
    return data.get("workflowStatus")


class GoodflagAPIError(Exception):
    """Exception levée lors d'erreurs avec l'API Goodflag."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class GoodflagClient:
    """Client pour interagir avec l'API Goodflag Workflow Manager."""

    def __init__(
        self,
        base_url: str | None = None,
        api_token: str | None = None,
        user_id: str | None = None,
    ):

        self.base_url = base_url or os.getenv("GOODFLAG_API_BASE")
        self.api_token = api_token or os.getenv("GOODFLAG_API_TOKEN")
        self.user_id = user_id or os.getenv("GOODFLAG_USER_ID")

        if not self.base_url:
            raise ValueError("GOODFLAG_API_BASE environment variable is required")
        if not self.api_token:
            raise ValueError("GOODFLAG_API_TOKEN environment variable is required")
        if not self.user_id:
            raise ValueError("GOODFLAG_USER_ID environment variable is required")

        self.base_url = self.base_url.rstrip("/") + "/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Effectue une requête HTTP avec gestion d'erreur."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error("Erreur API Goodflag: %s", str(e))
            status_code = (
                getattr(e.response, "status_code", None)
                if hasattr(e, "response")
                else None
            )
            response_data = None
            if hasattr(e, "response") and e.response is not None:
                try:
                    response_data = e.response.json()
                except ValueError:
                    response_data = {"text": e.response.text}
            raise GoodflagAPIError(str(e), status_code, response_data) from e

    def create_workflow(self, name: str, steps: list[Step]) -> dict:
        """
        Crée un nouveau workflow avec étapes d'approbation et de signature.

        Args:
            name: Nom du workflow
            steps: Liste des étapes du workflow

        Returns:
            dict contenant la réponse de l'API (incluant workflowId)
        """
        endpoint = f"/users/{self.user_id}/workflows"

        workflow_data = {
            "name": name,
            "steps": [
                {
                    "stepType": step["step_type"].value,
                    "recipients": [
                        {
                            "email": recipient["email"],
                            "firstName": recipient["first_name"],
                            "lastName": recipient["last_name"],
                            "consentPageId": (
                                SIGNATURE_CONSENT_PAGE_ID
                                if step["step_type"] == StepType.SIGNATURE
                                else None
                            ),
                            "preferredLocale": recipient.get("preferred_locale", "fr"),
                        }
                        for recipient in step["recipients"]
                    ],
                    "maxInvites": 3,
                }
                for step in steps
            ],
        }

        response = self._make_request(
            "POST", endpoint, headers=self.headers, json=workflow_data
        )
        return response.json()

    def start_workflow(self, workflow_id: str):
        endpoint = f"/workflows/{workflow_id}"

        response = self._make_request(
            "PATCH", endpoint, headers=self.headers, json={"workflowStatus": "started"}
        )
        if not response.ok:
            raise GoodflagAPIError(
                "Failed starting workflow %s" % workflow_id,
                response.status_code,
                response.json(),
            )

    def upload_document(
        self,
        workflow_id: str,
        file_path: str,
    ) -> dict:
        """
        Upload un document PDF dans un workflow.

        Args:
            workflow_id: ID du workflow
            file_path: Chemin vers le fichier PDF
        """
        if not os.path.exists(file_path):
            raise GoodflagAPIError(f"Le fichier {file_path} n'existe pas")

        endpoint = f"/workflows/{workflow_id}/parts"
        params = {
            "createDocuments": "true",
            "signatureProfileId": SIGNATURE_PROFILE_ID,
            "convertToPdf": "true",
            "pdf2pdfa": "forced",
        }

        headers = {"Authorization": f"Bearer {self.api_token}"}

        file_extension = os.path.splitext(file_path)[1]

        with open(file_path, "rb") as f:
            files = {
                "filename": (
                    f"document{file_extension}",
                    f,
                    mimetypes.guess_type(file_path)[0] or "application/pdf",
                )
            }
            response = self._make_request(
                "POST", endpoint=endpoint, headers=headers, files=files, params=params
            )

        return response.json()

    def create_viewer(
        self,
        document_id: str,
    ) -> dict:
        """
        Crée un viewer pour visualiser un document.

        Args:
            document_id: ID du document
        """
        endpoint = f"/documents/{document_id}/viewer"

        viewer_data = {
            "redirectUrl": REDIRECT_URL,
            "expired": int((timezone.now() + SIGNATURE_EXPIRED_TD).timestamp() * 1000),
        }

        response = self._make_request(
            "POST", endpoint, headers=self.headers, json=viewer_data
        )
        return response.json()

    def get_workflow_status(self, workflow_id: str) -> dict:
        """
        Récupère le statut d'un workflow.

        Args:
            workflow_id: ID du workflow

        """
        endpoint = f"/workflows/{workflow_id}"

        response = self._make_request("GET", endpoint, headers=self.headers)
        return response.json()

    def download_document(self, document_id: str, output_path: str) -> None:
        """
        Télécharge un document signé.

        Args:
            document_id: ID du document
            output_path: Chemin de sauvegarde du fichier
        """
        endpoint = f"/documents/{document_id}/download"

        headers = {"Authorization": f"Bearer {self.api_token}"}

        response = self._make_request("GET", endpoint, headers=headers)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info("Document téléchargé: %s", output_path)

    def retrieve_workflow(self, workflow_id: str) -> dict:
        endpoint = f"/workflows/{workflow_id}"
        response = self._make_request("GET", endpoint, headers=self.headers)
        return response.json()

    def retrieve_workflow_settings(self, workflow_id: str) -> dict:
        endpoint = f"/workflows/{workflow_id}/settings"
        response = self._make_request("GET", endpoint, headers=self.headers)
        return response.json()

    def list_consent_pages(self):
        endpoint = "/consentPages"
        response = self._make_request("GET", endpoint, headers=self.headers)
        return response.json()

    def list_signature_profiles(self):
        endpoint = "/signatureProfiles"
        response = self._make_request("GET", endpoint, headers=self.headers)
        return response.json()
