from rich.prompt import Prompt

from adapters.console_adapter import ConsoleAdapter
from core.hub import LunaHub


def main():
    console_adapter = ConsoleAdapter()
    luna_hub = LunaHub(console_adapter)

    user_id = "Jordan"
    while True:
        user_message = luna_hub.user_prompt()

        console_adapter.display_user_message(
            user_message,
            user_id
        )

        luna_response = luna_hub.process_message(user_message)

        console_adapter.display_assistant_message(
            luna_response
        )