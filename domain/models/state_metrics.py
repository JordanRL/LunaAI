from dataclasses import dataclass


@dataclass
class TimeMetrics:
    conversation_start: float
    conversation_last: float
    message_count: int
    turn_count: int
    average_time_to_user_response: float
    average_tokens_per_input: int
    average_tokens_per_output: int
    average_tokens_per_turn: int
