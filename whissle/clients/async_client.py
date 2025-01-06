from typing import List

import httpx

from ..models import (
    ASRModel,
    ASRModelList,
    LLMSummarizerResponse,
    MTResposne,
    STTResponse,
)
from ..options import WhissleClientOptions
from .errors import HttpError


class AsyncWhissleClient:
    def __init__(self, config: WhissleClientOptions):
        self._config = config
        self._httpx_client = httpx.AsyncClient(base_url=self._config.server_url)

    def _append_auth_token(self, url):
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}auth_token={self._config.auth_token}"

    async def authorized_get(self, url):
        """
        Perform an authorized API fetch with the necessary headers.

        Args:
            url (str): The API endpoint URL.

        Returns:
            Any: The API response JSON parsed into a Pydantic model.
        """
        headers = {
            "Content-Type": "application/json",
        }

        try:
            url = self._append_auth_token(url)
            response = await self._httpx_client.get(url, headers=headers)

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HttpError(e.response.status_code, e.response.text)

    async def authorized_post(self, url, file=None, data=None):
        headers = {}

        try:
            url = self._append_auth_token(url)
            if file:
                response = await self._httpx_client.post(
                    url=url,
                    headers=headers,
                    data=data or {},
                    files={
                        "audio": ("file", open(file, "rb"), "application/octet-stream")
                    },
                )
            elif data:
                response = await self._httpx_client.post(
                    url=url, headers={"Content-Type": "application/json"}, json=data
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise HttpError(e.response.status_code, e.response.text)

    async def list_asr_models(self) -> List[ASRModel]:
        response_data = await self.authorized_get("/list-asr-models")
        return response_data

    async def speech_to_text(
        self, audio_file_path, model_name: ASRModelList
    ) -> STTResponse:
        url = f"/conversation/STT?model_name={model_name}"
        response = await self.authorized_post(url, file=audio_file_path)
        return STTResponse(**response)

    async def machine_translation(
        self, text: str, source_language: str, target_language: str
    ) -> MTResposne:
        url = f"/MT?source_language={source_language}&target_language={target_language}"
        response = await self.authorized_post(url, data={"text": text})
        return MTResposne(**response)

    async def llm_text_summarizer(
        self, content: str, model_name: str, instruction: str
    ) -> LLMSummarizerResponse:
        url = "/llm-text-summarizer"
        response = await self.authorized_post(
            url,
            data={
                "content": content,
                "model_name": model_name,
                "instruction": instruction,
            },
        )
        return LLMSummarizerResponse(**response)
