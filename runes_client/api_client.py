import asyncio
import logging
from urllib.parse import urljoin

import aiohttp

from .config import (
    API_BASE_URL,
    URL_UPDATE_CONNECTION_STATUS,
    URL_UPDATE_CONNECTION_LOADED_STATUS,
    URL_CREATE_COMPUTE_CONTRACT,
    URL_ADD_CONNECTION_MAPPING,
    URL_GET_PENDING_MESSAGES,
    URL_UPDATE_MESSAGE_STATUS,
    URL_SEND_MESSAGE_RESPONSE,
)


class APIClient:
    CONNECTED_STATUS = 1

    def __init__(self, api_url):
        self.api_url = api_url

    async def connection_heartbeat(self, connection_token: str):
        heartbeat_url = urljoin(
            API_BASE_URL,
            URL_UPDATE_CONNECTION_STATUS.format(
                token=connection_token, connection_status=self.CONNECTED_STATUS
            ),
        )

        async with aiohttp.ClientSession() as session:
            async with session.put(heartbeat_url) as response:
                if response.status != 200:
                    logging.info(
                        f"Error updating status for client_id: {connection_token}. Status code: {response.status}"
                    )
                else:
                    logging.info(
                        f"Successfully updated status for client_id: {connection_token}"
                    )
                    return  # Exit the function on successful response

    async def create_compute_contract(self, token: str, data):
        print(f"CREATING CONTRACT {data}")

        # dict_data = data.to_dict()

        json_data = {
            "id": token,
            "data": data,
        }

        create_contract_url = urljoin(API_BASE_URL, URL_CREATE_COMPUTE_CONTRACT)

        max_retries = 3  # Maximum number of retries
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        create_contract_url,
                        json=json_data,
                    ) as response:
                        response_data = await response.text()
                        if response.status != 201:
                            print(
                                f"Error creating compute contract. Status code: {response.status}, Response: {response_data}"
                            )
                        else:
                            print(
                                f"Successfully created compute contract. Response: {response_data}"
                            )
                            return (
                                response_data  # Successful response, exit the function
                            )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.error(f"Compute Contract Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise  # Re-raise the last exception if all retries fail

            # TODO: MOVE THIS TO BYOC_API.PY

    async def add_connection_mapping(
        self,
        master_token: str,
        connection_token: str,
        name: str,
        description: str,
        connection_type: str,
    ):
        add_mapping_url = urljoin(API_BASE_URL, URL_ADD_CONNECTION_MAPPING)

        payload = {
            "master_token": master_token,
            "connection_token": connection_token,
            "connection_name": name,
            "connection_type": connection_type,
            "description": description,
        }

        max_retries = 3  # Define the maximum number of retries
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(add_mapping_url, json=payload) as response:
                        response_data = await response.text()
                        print("ADD_MAPPING_RES: " + str(response_data))
                        if response.status != 201:
                            print(
                                f"Error adding connection mapping. Status code: {response.status}, Response: {response_data}"
                            )
                        else:
                            print(
                                f"Successfully added connection mapping. Response: {response_data}"
                            )
                            return response_data  # Break out of the loop on success
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.error(
                    f"Add Connection Mapping Attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:  # Check if we've reached the max retries
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise  # Re-raise the last exception if all retries fail

    async def fetch_pending_requests(self, connection_token: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    urljoin(
                        API_BASE_URL,
                        URL_GET_PENDING_MESSAGES.format(
                            connection_token=connection_token
                        ),
                    )
                ) as response:
                    # Check response status. If not 200 OK, print error and continue.
                    if response.status != 200:
                        print(
                            f"Error fetching connection statuses. HTTP status: {response.status}"
                        )
                        return None

                    # Try parsing the response to JSON
                    data = await response.json()

                    return data

            except Exception as e:
                print(f"Unexpected error during check_connection_statuses: {e}")

    async def update_connection_loaded_status(
        self, connection_token: str, loaded: bool
    ) -> bool:
        update_url = urljoin(
            API_BASE_URL,
            URL_UPDATE_CONNECTION_LOADED_STATUS.format(token=connection_token),
        )

        data = {"loaded": loaded}

        async with aiohttp.ClientSession() as session:
            async with session.put(update_url, json=data) as response:
                if response.status != 200:
                    logging.info(
                        f"Error updating status for client_id: {connection_token}."
                    )
                    return False
                else:
                    logging.info(
                        f"Successfully updated status for client_id: {connection_token}"
                    )
                    return True

    async def update_message_status(self, token: str, message_id: str, new_status: str):
        print(f"UPDATING MESSAGE STATUS for id {message_id}")
        update_url = urljoin(
            API_BASE_URL,
            URL_UPDATE_MESSAGE_STATUS.format(token=token, message_id=message_id),
        )
        payload = {"status": new_status}

        max_retries = 3  # Define the maximum number of retries
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.patch(update_url, json=payload) as response:
                        response_data = await response.text()
                        if response.status != 200:
                            print(
                                f"Error updating status for message_id: {message_id} with token: {token}. Status code: {response.status}, Response: {response_data}"
                            )
                        else:
                            print(
                                f"Successfully updated status for message_id: {message_id} with token: {token}. Response: {response_data}"
                            )
                            return  # Exit the function on successful response
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.error(
                    f"Update Message Status Attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise  # Re-raise the last exception if all retries fail

    async def send_message_response(self, token: str, message_id: str, response: str):
        send_response_url = urljoin(API_BASE_URL, URL_SEND_MESSAGE_RESPONSE)

        payload = {
            "id": message_id,
            "token": token,
            "response": response,
            "status": "completed",
        }

        print("SENDING RESPONSE TO: " + str(send_response_url))
        print("SENDING RESPONSE: " + str(payload))

        max_retries = 3  # Define the maximum number of retries
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        send_response_url, json=payload
                    ) as response:
                        response_data = await response.text()
                        print("SEND_RESPONSE_STATUS: " + str(response_data))
                        if response.status != 200:
                            print(
                                f"Error responding to message_id: {message_id} with token: {token}. Status code: {response.status}, Response: {response_data}"
                            )
                        else:
                            print(
                                f"Successfully responded to message_id: {message_id} with token: {token}. Response: {response_data}"
                            )
                            return response_data  # Break out of the loop on success
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logging.error(
                    f"Send Message Response Attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:  # Check if we've reached the max retries
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise  # Re-raise the last exception if all retries fail
