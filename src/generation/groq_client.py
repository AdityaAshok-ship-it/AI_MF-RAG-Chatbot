import logging
import time
from src import config

logger = logging.getLogger("GroqClient")

GROQ_MODEL = "llama-3.1-8b-instant"
MAX_TOKENS = 512
TEMPERATURE = 0.1
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds; doubles each retry (2, 4, 8)

try:
    from groq import Groq, RateLimitError, APIConnectionError, APIStatusError
    GROQ_AVAILABLE = True
except ImportError:
    logger.warning("groq package not installed. GroqClient will be unavailable.")
    GROQ_AVAILABLE = False


class GroqClient:
    def __init__(self):
        if not GROQ_AVAILABLE:
            raise ImportError("Install the 'groq' package: pip install groq")

        api_key = config.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")

        self.client = Groq(api_key=api_key)
        self.model = GROQ_MODEL
        logger.info(f"GroqClient initialized with model: {self.model}")

    def generate(self, system_prompt: str, user_prompt: str,
                 max_tokens: int = MAX_TOKENS, temperature: float = TEMPERATURE) -> dict:
        """
        Send a prompt to Groq and return the response.
        Retries up to MAX_RETRIES times with exponential backoff on rate limit / connection errors.
        """
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Groq API call (attempt {attempt}/{MAX_RETRIES})...")
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                response_text = completion.choices[0].message.content.strip()
                logger.info("Groq API call succeeded.")
                return {
                    "response": response_text,
                    "model": completion.model,
                    "usage": {
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens,
                    }
                }

            except RateLimitError as e:
                last_error = e
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Rate limit hit. Retrying in {delay}s... ({e})")
                time.sleep(delay)

            except APIConnectionError as e:
                last_error = e
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Connection error. Retrying in {delay}s... ({e})")
                time.sleep(delay)

            except APIStatusError as e:
                # Non-retryable (e.g. 400 bad request, 401 auth)
                logger.error(f"Groq API status error (non-retryable): {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error calling Groq API: {e}")
                raise

        logger.error(f"Groq API failed after {MAX_RETRIES} retries. Last error: {last_error}")
        raise RuntimeError(
            "The assistant is experiencing high traffic. Please wait a moment and try again."
        ) from last_error
