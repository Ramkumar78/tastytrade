import logging
from httpx import Client
from tastytrade.utils import validate_and_parse, TastytradeError, validate_response

logger = logging.getLogger(__name__)

API_URL = "https://api.tastyworks.com"

class LegacySession:
    """
    Implements a Session-like interface using Username/Password login (Legacy API).
    Used to bypass the need for an OAuth Refresh Token if the user prefers direct credentials.
    """
    def __init__(self, login, password):
        self.base_url = API_URL
        self.sync_client = Client(base_url=self.base_url)
        # Alias for SDK compatibility if it accesses .client
        self.client = self.sync_client
        self.session_token = None
        self.login(login, password)

    def login(self, login, password):
        """
        Logs in using the legacy /sessions endpoint.
        """
        payload = {"login": login, "password": password}
        # Note: /sessions is V1.
        response = self.sync_client.post("/sessions", json=payload)

        if response.status_code == 201 or response.status_code == 200:
            json_body = response.json()
            token = None

            # Check common locations for session token in V1 response
            if "data" in json_body and "session-token" in json_body["data"]:
                token = json_body["data"]["session-token"]
            elif "context" in json_body and "session-token" in json_body["context"]:
                 token = json_body["context"]["session-token"]

            if token:
                self.session_token = token
                # For Legacy Session Token, typically Authorization: <token> (no Bearer)
                self.sync_client.headers.update({"Authorization": token})
                logger.info("Legacy Login Successful via /sessions.")
            else:
                logger.error(f"Login successful but no token found in response: {json_body}")
                raise TastytradeError("Could not retrieve session token from login response.")
        else:
            validate_response(response)

    def validate(self) -> bool:
        """
        Validates the current session.
        """
        if not self.session_token:
            return False
        response = self.sync_client.post("/sessions/validate")
        return response.status_code // 100 == 2

    def _get(self, url: str, **kwargs) -> dict:
        response = self.sync_client.get(url, **kwargs)
        return validate_and_parse(response)

    def _post(self, url: str, **kwargs) -> dict:
        response = self.sync_client.post(url, **kwargs)
        return validate_and_parse(response)

    def _put(self, url: str, **kwargs) -> dict:
        response = self.sync_client.put(url, **kwargs)
        return validate_and_parse(response)

    def _delete(self, url: str, **kwargs) -> None:
        response = self.sync_client.delete(url, **kwargs)
        validate_response(response)
