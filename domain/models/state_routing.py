from dataclasses import dataclass, field
from typing import Callable, List

from domain.models.enums import AgentType


@dataclass
class StateRouting:
    # Agent lists
    pre_routing_agents: List[AgentType] = field(default_factory=list)
    routing_agents: List[AgentType] = field(default_factory=list)
    post_routing_agents: List[AgentType] = field(default_factory=list)
    output_agent: AgentType = AgentType.OUTPUTTER

    # Formatting callables
    pre_routing_formatter: Callable = None
    routing_formatter: Callable = None
    post_routing_formatter: Callable = None
    output_formatter: Callable = None
