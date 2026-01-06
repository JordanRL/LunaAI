from enum import Enum

import anthropic
import openai
from google import genai


class ClientType(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class Client:
    def __init__(self, api_key: str, api_type: ClientType):
        self.api_key = api_key
        self.api_type = api_type
        self.client = None
        if api_type == ClientType.ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif api_type == ClientType.OPENAI:
            self.client = openai.OpenAI(api_key=self.api_key)
        elif api_type == ClientType.GEMINI:
            self.client = genai.Client(api_key=self.api_key)
