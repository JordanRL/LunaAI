from rich.prompt import Prompt

from adapters.console_adapter import ConsoleAdapter
from adapters.logging_adapter import LoggingAdapter
from core.hub import LunaHub
from services.conversation_service import ConversationService
from services.emotion_service import EmotionService
from services.user_service import UserService


def main():
    console_adapter = ConsoleAdapter()
    user_service = UserService()
    conversation_service = ConversationService(user_service)
    emotion_service = EmotionService()
    logging_adapter = LoggingAdapter
    luna_hub = LunaHub(
        console_adapter=console_adapter,
        conversation_service=conversation_service,
        emotion_service=emotion_service,
        user_service=user_service
    )

    user_id = "Jordan"
    while True:
        user_message = luna_hub.user_prompt()

        console_adapter.display_user_message(
            user_message,
            user_id
        )

        luna_response = luna_hub.process_message(user_message, user_id)

        console_adapter.display_assistant_message(
            luna_response
        )

if __name__ == "__main__":
    main()