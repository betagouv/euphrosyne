import logging
import os
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GoodflagAPIError(Exception):
    """Exception levée lors d'erreurs avec l'API Goodflag."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class GoodflagClient:
    """Client pour interagir avec l'API Goodflag Workflow Manager."""
    
    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None):
        self.base_url = base_url or os.getenv("GOODFLAG_API_BASE")
        self.api_token = api_token or os.getenv("GOODFLAG_API_TOKEN")
        
        if not self.base_url:
            raise ValueError("GOODFLAG_API_BASE environment variable is required")
        if not self.api_token:
            raise ValueError("GOODFLAG_API_TOKEN environment variable is required")
            
        self.base_url = self.base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Effectue une requête HTTP avec gestion d'erreur."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API Goodflag: {e}")
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            response_data = None
            if hasattr(e, 'response') and e.response is not None:
                try:
                    response_data = e.response.json()
                except ValueError:
                    response_data = {"text": e.response.text}
            raise GoodflagAPIError(str(e), status_code, response_data)
    
    def create_workflow(self, user_id: str, name: str, recipients: List[str]) -> Dict:
        """
        Crée un nouveau workflow avec étapes d'approbation et de signature.
        
        Args:
            user_id: ID de l'utilisateur propriétaire du workflow
            name: Nom du workflow
            recipients: Liste des destinataires pour l'approbation et la signature
        
        Returns:
            Dict contenant la réponse de l'API (incluant workflowId)
        """
        endpoint = f"/api/users/{user_id}/workflows"
        
        workflow_data = {
            "name": name,
            "steps": [
                {
                    "stepType": "approval",
                    "recipients": recipients
                },
                {
                    "stepType": "signature", 
                    "recipients": recipients
                }
            ]
        }
        
        response = self._make_request("POST", endpoint, headers=self.headers, json=workflow_data)
        return response.json()
    
    def upload_document(self, workflow_id: str, file_path: str, signature_profile_id: str = "sip_default") -> Dict:
        """
        Upload un document PDF dans un workflow.
        
        Args:
            workflow_id: ID du workflow
            file_path: Chemin vers le fichier PDF
            signature_profile_id: ID du profil de signature
        
        Returns:
            Dict contenant la réponse de l'API (incluant documentId)
        """
        if not os.path.exists(file_path):
            raise GoodflagAPIError(f"Le fichier {file_path} n'existe pas")
        
        endpoint = f"/api/workflows/{workflow_id}/parts"
        params = {
            "createDocuments": "true",
            "signatureProfileId": signature_profile_id
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self._make_request("POST", endpoint, headers=headers, files=files, params=params)
        
        return response.json()
    
    def create_viewer(self, document_id: str, redirect_url: str, expire_ts: int) -> Dict:
        """
        Crée un viewer pour visualiser un document.
        
        Args:
            document_id: ID du document
            redirect_url: URL de redirection après visualisation
            expire_ts: Timestamp d'expiration (en millisecondes)
        
        Returns:
            Dict contenant viewerUrl
        """
        endpoint = f"/api/documents/{document_id}/viewer"
        
        viewer_data = {
            "redirectUrl": redirect_url,
            "expired": expire_ts
        }
        
        response = self._make_request("POST", endpoint, headers=self.headers, json=viewer_data)
        return response.json()
    
    def get_workflow_status(self, workflow_id: str) -> Dict:
        """
        Récupère le statut d'un workflow.
        
        Args:
            workflow_id: ID du workflow
        
        Returns:
            Dict contenant le statut complet du workflow
        """
        endpoint = f"/api/workflows/{workflow_id}"
        
        response = self._make_request("GET", endpoint, headers=self.headers)
        return response.json()
    
    def download_document(self, document_id: str, output_path: str) -> None:
        """
        Télécharge un document signé.
        
        Args:
            document_id: ID du document
            output_path: Chemin de sauvegarde du fichier
        """
        endpoint = f"/api/documents/{document_id}/download"
        
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        response = self._make_request("GET", endpoint, headers=headers)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Document téléchargé: {output_path}")