import os
from anthropic import Anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
