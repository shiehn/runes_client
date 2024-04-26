# Existing imports...
import json
import os
import subprocess
from urllib.parse import urlparse, urlsplit

from ..api_client import APIClient
from ..config import API_BASE_URL
from ..dn_tracer import SentryEventLogger, DNSystemType, DNMsgStage, DNTag
from ..file_uploader import FileUploader
from ..utils.audio_utils import process_audio_file
from ..utils.file_type_classifier import FileTypeClassifier


# ResultsHandler class to handle the results
class ResultsHandler:
    def __init__(
        self,
        websocket,
        token,
        target_sample_rate=41000,
        target_bit_depth=16,
        target_channels=2,
        target_format="wav",
    ):
        self.websocket = websocket
        self.token = token
        self.message_id = None
        self.errors = []
        self.files = []
        self.logs = ""
        self.messages = []
        self.file_uploader = FileUploader()
        self.dn_tracer = SentryEventLogger(DNSystemType.DN_CLIENT.value)

        # Check if ffmpeg is installed
        self.ffmpeg_installed = self.check_ffmpeg()

        # Default target audio settings
        self.target_sample_rate = target_sample_rate
        self.target_bit_depth = target_bit_depth
        self.target_channels = target_channels
        self.target_format = target_format

    def check_ffmpeg(self):
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            return True
        except FileNotFoundError:
            print(
                "ffmpeg is not installed. Please install ffmpeg for audio processing."
            )
            return False

    def update_token(self, token):
        self.token = token

    async def add_error(self, error):
        self.errors.append(error)
        return True

    def set_message_id(self, message_id):
        self.message_id = message_id

    async def add_file_url(self, file_url: str, file_type: str):
        # List of supported file types
        supported_file_types = [
            "audio",
            "midi",
            "text",
            "video",
            "image",
        ]

        # Check if the file type is supported
        if file_type.lower() not in supported_file_types:
            await self.add_error(f"File type {file_type} is not supported.")
            return False

        # Validate URL
        try:
            parsed_url = urlparse(file_url)
            if not (parsed_url.scheme and parsed_url.netloc):
                raise ValueError("Invalid URL")
        except Exception as e:
            await self.add_error(f"Invalid file URL: {e}")
            return False

        # Extract base name from URL
        file_name = os.path.basename(parsed_url.path)

        # If the extracted base name is empty or invalid, set a default name
        if not file_name:
            file_name = "default_filename"

        # Add the file to the list
        self.files.append(
            {
                "name": file_name,
                "url": file_url,
                "type": file_type,
            }
        )

        return True

    async def add_file(self, file_path):
        classifier = FileTypeClassifier()
        input_type = classifier.classify(file_path)

        if input_type == "audio":
            if not self.ffmpeg_installed:
                error_message = (
                    "FFmpeg is not installed, which is required for processing audio files.\n"
                    "To install FFmpeg, follow these instructions:\n"
                    "- On macOS: Use Homebrew by running 'brew install ffmpeg' in the terminal.\n"
                    "- On Linux (Debian/Ubuntu): Run 'sudo apt-get install ffmpeg' in the terminal.\n"
                    "- On Linux (Fedora): Run 'sudo dnf install ffmpeg' in the terminal.\n"
                    "- On Linux (Arch Linux): Run 'sudo pacman -S ffmpeg' in the terminal.\n"
                    "For other operating systems or more detailed instructions, visit the FFmpeg website: https://ffmpeg.org/download.html"
                )
                print(error_message)  # TODO how do errors get reported to the user?
                await self.add_error(error_message)
                return False

            converted_file_path = None
            try:
                # Check and convert audio file if necessary
                converted_file_path = process_audio_file(
                    file_path,
                    target_format=self.target_format,
                    target_sample_rate=self.target_sample_rate,
                    target_bit_depth=self.target_bit_depth,
                    target_channels=self.target_channels,
                )

                self.dn_tracer.log_event(
                    self.token,
                    {
                        DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONVERT_UPLOAD.value,
                        DNTag.DNMsg.value: str(converted_file_path),
                    },
                )

            except Exception as e:
                self.dn_tracer.log_error(
                    self.token,
                    {
                        DNTag.DNMsgStage.value: DNMsgStage.CLIENT_CONVERT_UPLOAD.value,
                        DNTag.DNMsg.value: str(e),
                    },
                )
                await self.add_error(str(e))

        elif input_type == "midi":
            converted_file_path = file_path
        elif input_type == "image":
            converted_file_path = file_path
        else:
            converted_file_path = file_path

        try:
            file_url = await self.file_uploader.upload(
                converted_file_path, os.path.splitext(converted_file_path)[1][1:]
            )

            self.files.append(
                {
                    "name": os.path.basename(converted_file_path),
                    "url": file_url,
                    "type": input_type,
                }
            )

            self.dn_tracer.log_event(
                self.token,
                {
                    DNTag.DNMsgStage.value: DNMsgStage.CLIENT_UPLOAD_ASSET.value,
                    DNTag.DNMsg.value: file_url,
                },
            )
        except Exception as e:
            self.dn_tracer.log_error(
                self.token,
                {
                    DNTag.DNMsgStage.value: DNMsgStage.CLIENT_UPLOAD_ASSET.value,
                    DNTag.DNMsg.value: str(e),
                },
            )
            await self.add_error(str(e))

        return True

    async def add_message(self, message):
        self.messages.append(message)
        return True

    async def add_log(self, log):
        self.logs += log
        return True

    def clear_outputs(self):
        """Clears the output attributes of the ResultsHandler instance."""
        self.message_id = None
        self.errors = []
        self.files = []
        self.logs = ""
        self.messages = []

    async def send(self):
        status = "completed" if not self.errors else "error"

        print("STATUS: " + status)

        data = {
            "response": {
                "files": self.files,
                "error": ", ".join(self.errors) if self.errors else None,
                "logs": self.logs,
                "message": ", ".join(self.messages) if self.messages else None,
                "status": status,
            }
        }

        if self.message_id:
            data["response"]["id"] = self.message_id

        send_msg = {"token": self.token, "type": "results", "data": data}

        print("API_CLIENT- start")
        api_client = APIClient(API_BASE_URL)
        await api_client.send_message_response(
            self.token, self.message_id, data["response"]
        )
        print("API_CLIENT- end")

        # await self.websocket.send(json.dumps(send_msg))

        self.dn_tracer.log_event(
            self.token,
            {
                DNTag.DNMsgStage.value: DNMsgStage.CLIENT_SEND_RESULTS_MSG.value,
                DNTag.DNMsg.value: json.dumps(send_msg),
            },
        )

        return send_msg


def handle_the_results():
    return True
