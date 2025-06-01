"""Python client for TTS.Monster API.

https://docs.tts.monster/introduction"""

from typing import Dict
from importlib.metadata import version
from datetime import timedelta
import time
from http import HTTPStatus
from json import JSONDecodeError

import requests
from requests.exceptions import HTTPError
from .ratelimiter import RateLimit, Store
from .exceptions import TTSMAPIError

class Client:
    """TTS.Monster API client
    
    This class provides methods to interact with the TTS.Monster API, including 'generate'ing 
    text-to-speech audio, retrieving 'user' information, and listing available 'voices'.
    
    An attempt is made to avoid exceeding endpoint rate limits by tracking and rate limiting usage locally.

    By default, the 'generate' endpoint user account character quota is enforced for convenience. Requests 
    that would exceed the character quota will raise a TTSMAPIError. If enforcement is disabled, you 
    will be subject to requests being rejected by TTS.Monster (free plan) or overage fees (paid plans).
    
    The 'voice-cloning' endpoint is not currently implemented because of its beta status and complexity."""

    def __init__(self, api_key: str, enforce_char_quota: bool = True):
        """
        Initialize a TTS.Monster API Client object.

        Args:
            api_key (str): Your TTS.Monster API key. Store it securely, such as in an environment variable.
            enforce_char_quota (bool): Whether to enforce the TTSM 'generate' endpoint character quota (default True).
        Raises:
            TTSMAPIError: If the API key is invalid, or API responses are otherwise not as expected.
            HTTPError: If 'user' endpoint returns an unrecoverable non-2XX HTTP status code.
        """
        self._url: str = "https://api.console.tts.monster/"
        self._timeout: float = 60
        self._retries: int = 3
        self._api_key: str = api_key
        self._version: str = version("ttsmapi")
        self._name: str = "Python TTSM-API"
        self._user_agent: str = f"{self._name}/{self._version}"
        #TODO: move rate limiting to a real library like token-throttle later
        self._rate_limit_store: Store = Store()
        self.user_rate_limit: RateLimit = RateLimit(count=50, period=timedelta(seconds=60))
        self.voices_rate_limit: RateLimit = RateLimit(count=50, period=timedelta(seconds=60))
        self.generate_rate_limit: RateLimit = RateLimit(count=30, period=timedelta(seconds=60))
        self.generate_character_limit: int = 500
        self.enforce_char_quota: bool = enforce_char_quota
        self.generate_character_quota: int
        self.generate_character_usage: int

        if self.enforce_char_quota:
            try:
                user_info: Dict = self.get_user()
            except HTTPError as e:
                if e.response.status_code == HTTPStatus.UNAUTHORIZED:
                    raise TTSMAPIError("Invalid API key") from e
                raise TTSMAPIError("Failed to get user info from TTS.Monster API") from e
            
            if 'character_allowance' not in user_info:
                raise TTSMAPIError("User info does not contain 'character_allowance'")
            self.generate_character_quota = user_info['character_allowance']
            if 'character_usage' not in user_info:
                raise TTSMAPIError("User info does not contain 'character_usage'")
            self.generate_character_usage = user_info['character_usage']

    def post(self, endpoint: str, rate_limit: RateLimit, ep_json: Dict|None = None) -> Dict:
        """Set up and perform a Requests POST for a given TTS.Monster endpoint.

        Args:
            endpoint (str): The endpoint to POST to, e.g. 'generate', 'user', 'voices'.
            rate_limit (RateLimit): The RateLimit object for the endpoint.
            ep_json (Dict|None): The JSON payload to send in the POST request, if any (default None).
        Returns:
            Dict: The JSON response from the TTS.Monster API.
        Raises:
            TTSMAPIError: If valid JSON is not in the response.
            HTTPError: If the API returns an unrecoverable non-2XX HTTP status code.
        """
        full_url: str = self._url + endpoint
        headers: Dict = {'User-Agent': self._user_agent, 'Authorization': self._api_key}

        rate_limited: bool = self._rate_limit_store.update(full_url, rate_limit)
        if rate_limited:
            time.sleep(rate_limit.period.total_seconds())

        response: requests.Response = requests.Response()
        for _ in range(self._retries):
            try:
                response = requests.post(url=full_url, timeout=self._timeout, headers=headers, json=ep_json)
                response.raise_for_status()
            except HTTPError as e:
                if e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    time.sleep(rate_limit.period.total_seconds())
                    continue
                raise

        try:
            response_json: Dict = response.json()
        except (ValueError, JSONDecodeError) as e:
            raise TTSMAPIError("Invalid/no JSON in response") from e

        return response_json

    def generate(self, voice_id: str, message: str, return_usage: bool = True) -> Dict:
        """TTS.Monster 'generate' endpoint (POST)
        https://docs.tts.monster/endpoint/generate

        Args:
            voice_id (str): The TTS.Monster ID (not name) of the voice to use for TTS.
            message (str): The text to be read.
            return_usage (bool): Whether to return character usage in the response (default True).
        Returns:
            Dict: The JSON response containing the details of the generated audio.
        Raises:
            TTSMAPIError: If the message exceeds the character limit, or if the message would exceed the character quota.
            HTTPError: If the API returns an unrecoverable non-2XX HTTP status code.
        """
        ep_json: Dict = {'voice_id': voice_id,
                        'message': message,
                        'return_usage': return_usage}

        if len(message) > self.generate_character_limit:
            raise TTSMAPIError(f"Message exceeds character limit of {self.generate_character_limit} characters.")
        if self.enforce_char_quota:
            if self.generate_character_usage + len(message) > self.generate_character_quota:
                raise TTSMAPIError(f"Message of len {len(message)} would exceed TTSM character usage quota of "
                                    f"{self.generate_character_usage}/{self.generate_character_quota} characters.")

        response_json: Dict = self.post(endpoint="generate", ep_json=ep_json, rate_limit=self.generate_rate_limit)

        self.generate_character_usage = response_json['characterUsage']

        return response_json

    def get_user(self) -> Dict:
        """TTS. Monster [get] 'user' endpoint (POST)
        https://docs.tts.monster/endpoint/get-user

        Returns:
            Dict: The JSON response containing the details of the user's subscription.
        Raises:
            TTSMAPIError: If valid JSON is not in the response.
            HTTPError: If the API returns an unrecoverable non-2XX HTTP status code.
        """
        response_json: Dict = self.post(endpoint="user", rate_limit=self.user_rate_limit)
        return response_json

    def get_voices(self) -> Dict:
        """TTS.Monster [get] 'voices' endpoint (POST)
        https://docs.tts.monster/endpoint/get-voices

        Returns:
            Dict: The JSON response containing a list of available public voices
                  and a list of available private custom voices.
        Raises:
            TTSMAPIError: If valid JSON is not in the response.
            HTTPError: If the API returns an unrecoverable non-2XX HTTP status code.
        """
        response_json: Dict = self.post(endpoint="voices", rate_limit=self.voices_rate_limit)
        return response_json
