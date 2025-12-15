from typing import Optional
from agents import set_default_openai_client
import httpx
import openai
import logging
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger("app")


class RateLimitInfo(BaseModel):
    limit_requests: Optional[int]
    remaining_requests: Optional[int]
    limit_tokens: Optional[int]
    remaining_tokens: Optional[int]
    reset_token_time: Optional[str]


class OpenAISingleton:
    _instance = None

    rate_limits = {}
    _last_update_timestamp = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OpenAISingleton, cls).__new__(cls)

            openai_async_client = openai.DefaultAsyncHttpxClient()
            openai_async_client.event_hooks["response"].append(
                cls.capture_rate_limits_hook
            )

            custom_openai_client = openai.AsyncOpenAI(
                http_client=openai_async_client,
            )
            print("✅ OpenAI client with rate limit hook instantiated.")
            # Set this as the default client for the Agents SDK
            set_default_openai_client(custom_openai_client)
            # cls._instance.client = OpenAIClient(*args, **kwargs)
        return cls._instance

    @classmethod
    async def capture_rate_limits_hook(cls, response: httpx.Response):
        """
        A response hook that captures x-ratelimit-* headers and stores them.
        Must be async when using AsyncOpenAI client.
        Only updates if this response is more recent than the last stored value.
        """
        headers = response.headers

        # Get the response timestamp (current time as proxy since responses don't have explicit timestamps)
        current_timestamp = datetime.now()

        # Check if we should update (only if this is newer than last update or first time)
        if (
            cls._last_update_timestamp is None
            or current_timestamp > cls._last_update_timestamp
        ):
            # Get remaining requests to determine if this is more recent
            remaining_requests = headers.get("x-ratelimit-remaining-requests")

            # If we have previous data, only update if remaining count is lower or equal (more recent)
            # Lower remaining = more recent request
            should_update = True

            if should_update:
                print("🔄 Updating OpenAI rate limit info from response headers.")
                cls.rate_limits["limit-requests"] = headers.get(
                    "x-ratelimit-limit-requests"
                )
                cls.rate_limits["remaining-requests"] = remaining_requests
                cls.rate_limits["limit-tokens"] = headers.get(
                    "x-ratelimit-limit-tokens"
                )
                cls.rate_limits["remaining-tokens"] = headers.get(
                    "x-ratelimit-remaining-tokens"
                )
                cls.rate_limits["reset-token-time"] = headers.get(
                    "x-ratelimit-reset-tokens"
                )
                cls._last_update_timestamp = current_timestamp

    def get_client(self):
        return self._instance.client

    @classmethod
    def get_reset_time_seconds(cls) -> int:
        """
        Parse OpenAI's reset time format to seconds from stored rate limits.

        Formats:
        - "24.555s" -> 24 seconds
        - "6m0s" -> 360 seconds
        - "1m30.5s" -> 90 seconds

        Returns:
            Integer seconds, or 60 if parsing fails or no reset time available
        """
        reset_time_str = cls.rate_limits.get("reset-token-time")

        if not reset_time_str:
            return 60

        try:
            total_seconds = 0

            # Check if it contains minutes
            if "m" in reset_time_str:
                # Format: "6m0s" or "1m30.5s"
                parts = reset_time_str.split("m")
                if len(parts) == 2:
                    # Parse minutes
                    minutes = int(parts[0])
                    total_seconds += minutes * 60

                    # Parse seconds part (remove 's' suffix)
                    seconds_part = parts[1].rstrip("s")
                    if seconds_part:
                        total_seconds += float(seconds_part)
            else:
                # Format: "24.555s"
                seconds_part = reset_time_str.rstrip("s")
                total_seconds = float(seconds_part)

            return int(total_seconds)

        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(
                f"Failed to parse reset time '{reset_time_str}', defaulting to 60s",
                extra={
                    "context": "get_reset_time_seconds",
                    "reset_time_str": reset_time_str,
                    "error": str(e),
                },
            )
            return 60

    @classmethod
    def get_rate_limits(cls) -> RateLimitInfo:
        return RateLimitInfo(
            limit_requests=(
                int(cls.rate_limits.get("limit-requests"))
                if cls.rate_limits.get("limit-requests") is not None
                else None
            ),
            remaining_requests=(
                int(cls.rate_limits.get("remaining-requests"))
                if cls.rate_limits.get("remaining-requests") is not None
                else None
            ),
            limit_tokens=(
                int(cls.rate_limits.get("limit-tokens"))
                if cls.rate_limits.get("limit-tokens") is not None
                else None
            ),
            remaining_tokens=(
                int(cls.rate_limits.get("remaining-tokens"))
                if cls.rate_limits.get("remaining-tokens") is not None
                else None
            ),
            reset_token_time=(
                cls.rate_limits.get("reset-token-time")
                if cls.rate_limits.get("reset-token-time") is not None
                else None
            ),
        )
