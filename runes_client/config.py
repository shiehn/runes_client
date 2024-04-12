import os

# --------- PRODUCTION SETTINGS ----------------
SOCKET_IP = os.getenv("DN_CLIENT_SOCKET_IP", "signalsandsorceryapi.com")
API_BASE_URL = os.getenv("DN_CLIENT_API_BASE_URL", "https://signalsandsorceryapi.com")
SENTRY_API_KEY = os.getenv(
    "DN_CLIENT_SENTRY_API_KEY",
    "https://dbbf2855a707e0448957ad77111449c3@o4506379662131200.ingest.sentry.io/4506379670847488",
)
SOCKET_PORT = os.getenv("DN_CLIENT_SOCKET_PORT", "8765")
STORAGE_BUCKET_PATH = os.getenv(
    "DN_CLIENT_STORAGE_BUCKET", "https://storage.googleapis.com/byoc-file-transfer/"
)

# API URLs
URL_UPDATE_CONNECTION_STATUS = "api/hub/connection/compute/{token}/{connection_status}/"
URL_UPDATE_CONNECTION_LOADED_STATUS = "api/hub/connections/{token}/loaded/"
URL_GET_CONNECTIONS = "api/hub/connections/{token}/"
URL_ADD_CONNECTION_MAPPING = "api/hub/connection_mappings/"
URL_CREATE_COMPUTE_CONTRACT = "api/hub/compute/contract/"
URL_GET_COMPUTE_CONTRACT = "api/hub/compute/contract/{token}/"
URL_GET_PENDING_MESSAGES = "api/hub/get_latest_pending_messages/{connection_token}/"
URL_UPDATE_MESSAGE_STATUS = "api/hub/update_message_status/{token}/{message_id}/"
URL_SEND_MESSAGE_RESPONSE = "api/hub/reply_to_message/"
