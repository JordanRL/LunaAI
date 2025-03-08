from adapters.console_adapter import ConsoleAdapter
from adapters.elasticsearch_adapter import ElasticsearchAdapter
from adapters.logging_adapter import LoggingAdapter
from core.hub import LunaHub
from services.conversation_service import ConversationService
from services.emotion_service import EmotionService
from services.memory_service import MemoryService
from services.user_service import UserService


def main():
    console_adapter = ConsoleAdapter()
    es_adapter = ElasticsearchAdapter()
    user_service = UserService(es_adapter)
    conversation_service = ConversationService(user_service)
    emotion_service = EmotionService()
    logging_adapter = LoggingAdapter

    # Import here to avoid circular imports
    from services.prompt_service import PromptService

    prompt_service = PromptService()

    try:
        # Try to initialize the MemoryService
        memory_service = MemoryService(es_adapter)
        print("Memory service initialized successfully")
    except Exception as e:
        print(f"Memory service initialization failed: {str(e)}")
        memory_service = None

    luna_hub = LunaHub(
        console_adapter=console_adapter,
        conversation_service=conversation_service,
        emotion_service=emotion_service,
        prompt_service=prompt_service,
        user_service=user_service,
        memory_service=memory_service,
    )

    user_id = "Jordan"
    while True:
        user_message = luna_hub.user_prompt()

        console_adapter.display_user_message(user_message, user_id)

        luna_response = luna_hub.process_message(user_message, user_id)

        console_adapter.display_assistant_message(luna_response)


if __name__ == "__main__":
    main()
