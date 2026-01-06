from domain.models.enums import AgentType
from domain.models.messages import Message
from domain.models.state_mental import MentalState
from domain.models.state_metrics import TimeMetrics
from domain.models.state_routing import StateRouting
from services.conversation_service import ConversationService
from services.emotion_service import EmotionService
from services.time_awareness_service import TimeAwarenessService


class ContextStateService:
    conversation_service: ConversationService
    time_awareness_service: TimeAwarenessService
    emotion_service: EmotionService

    def __init__(
        self,
        conversation_service: ConversationService,
        time_awareness_service: TimeAwarenessService,
        emotion_service: EmotionService,
    ):
        self.conversation_service = conversation_service
        self.time_awareness_service = time_awareness_service
        self.emotion_service = emotion_service
        self.mental_state = MentalState(mental_energy=1.0, social_energy=1.0, cognitive_load=0.0)

    def update_mental_state(self, time_metrics: TimeMetrics):
        mental_energy_adj = 0.1
        social_energy_adj = 0.08

        if time_metrics.turn_count > 10:
            social_energy_adj -= 0.05 * (time_metrics.turn_count - 10)

        # TODO: Finish

        # if time_metrics.

    def record_conversation_message(self, conversation_id: str, message: Message):
        self.conversation_service.add_message(conversation_id, message)

    def get_state_based_routing(self):
        emotion_label = self.emotion_service.get_emotion_label()

    def _base_routing(self):
        return StateRouting(routing_agents=[AgentType.DISPATCHER])
