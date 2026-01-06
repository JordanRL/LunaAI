"""
Comprehensive configurations for generating synthetic conversational data
with diverse personality traits, scenarios, and conversation structures.
"""

# Conversation scenarios with context and potential dynamics
CONVERSATION_SCENARIOS = {
    "casual_meeting": {
        "context": "Two acquaintances meeting unexpectedly in a public place",
        "typical_topics": [
            "catching up",
            "mutual friends",
            "recent events",
            "weather",
            "small talk",
        ],
        "social_dynamics": "low-pressure, friendly, potentially brief",
    },
    "coffee_date": {
        "context": "Two people meeting for coffee, either as friends or potential romantic partners",
        "typical_topics": [
            "personal interests",
            "background",
            "opinions",
            "future plans",
            "shared experiences",
        ],
        "social_dynamics": "getting-to-know-you, evaluative, impression management",
    },
    "job_interview": {
        "context": "Formal conversation between interviewer and job candidate",
        "typical_topics": [
            "work experience",
            "skills",
            "hypothetical scenarios",
            "company fit",
            "career goals",
        ],
        "social_dynamics": "evaluative, power imbalance, professional boundaries",
    },
    "group_project": {
        "context": "Team members discussing work on a shared project or assignment",
        "typical_topics": ["task division", "deadlines", "ideas", "concerns", "coordination"],
        "social_dynamics": "collaborative, problem-solving, potential leadership dynamics",
    },
    "customer_service": {
        "context": "Interaction between customer and service representative",
        "typical_topics": ["product issues", "solutions", "policies", "requests", "complaints"],
        "social_dynamics": "service-oriented, potential tension, resolution-focused",
    },
    "friend_conflict": {
        "context": "Friends discussing a disagreement or misunderstanding",
        "typical_topics": [
            "hurt feelings",
            "explanations",
            "perceptions",
            "resolution",
            "apologies",
        ],
        "social_dynamics": "emotional, relationship maintenance, vulnerability",
    },
    "family_dinner": {
        "context": "Family members conversing during a meal",
        "typical_topics": [
            "daily activities",
            "family news",
            "shared memories",
            "future events",
            "opinions",
        ],
        "social_dynamics": "familiar, established roles, mixture of depth and small talk",
    },
    "colleague_lunch": {
        "context": "Coworkers chatting during a lunch break",
        "typical_topics": [
            "work projects",
            "office gossip",
            "weekend plans",
            "shared interests",
            "work-life balance",
        ],
        "social_dynamics": "semi-professional, relationship building, information exchange",
    },
    "party_conversation": {
        "context": "Conversation at a social gathering or party",
        "typical_topics": ["introductions", "connections", "interests", "light topics", "humor"],
        "social_dynamics": "social networking, impression management, potentially superficial",
    },
    "doctor_visit": {
        "context": "Patient and doctor during a medical appointment",
        "typical_topics": [
            "symptoms",
            "medical history",
            "treatment options",
            "health concerns",
            "recommendations",
        ],
        "social_dynamics": "expertise-based, information gathering, care-focused",
    },
    "roommate_discussion": {
        "context": "Roommates discussing living arrangements or issues",
        "typical_topics": [
            "shared responsibilities",
            "schedules",
            "preferences",
            "compromises",
            "finances",
        ],
        "social_dynamics": "negotiation, boundary setting, shared environment management",
    },
    "first_date": {
        "context": "Two people meeting for the first time in a romantic context",
        "typical_topics": [
            "personal background",
            "interests",
            "values",
            "light personal disclosure",
            "humor",
        ],
        "social_dynamics": "evaluative, impression management, attraction assessment",
    },
    "teacher_student": {
        "context": "Interaction between educator and student",
        "typical_topics": [
            "learning material",
            "questions",
            "feedback",
            "academic progress",
            "explanations",
        ],
        "social_dynamics": "instructional, mentorship, knowledge transfer",
    },
    "therapy_session": {
        "context": "Conversation between therapist and client",
        "typical_topics": [
            "personal challenges",
            "feelings",
            "coping strategies",
            "insights",
            "goals",
        ],
        "social_dynamics": "supportive, exploration, professional guidance",
    },
    "business_negotiation": {
        "context": "Representatives from different organizations discussing terms",
        "typical_topics": ["offers", "terms", "compromises", "benefits", "constraints"],
        "social_dynamics": "strategic, potentially competitive, outcome-focused",
    },
}

# Conversation approaches that modify the basic structure or flow
CONVERSATION_APPROACHES = {
    "standard_dialogue": {
        "structure": "Balanced turn-taking with typical question-answer patterns",
        "suitable_for": "Most everyday conversations and scenarios",
        "typical_length": "5-15 exchanges",
    },
    "intense_discussion": {
        "structure": "Deeper exchanges with longer turns and more substantive content",
        "suitable_for": "Important topics, intellectual discussions, or emotional conversations",
        "typical_length": "10-20 exchanges with longer individual turns",
    },
    "asymmetric_dialogue": {
        "structure": "One person speaks significantly more than the other",
        "suitable_for": "Expert explanations, venting sessions, or status differences",
        "typical_length": "5-15 exchanges with imbalanced contributions",
    },
    "interview_style": {
        "structure": "One person primarily asks questions, the other answers",
        "suitable_for": "Information gathering, job interviews, or journalistic contexts",
        "typical_length": "8-20 question-answer pairs",
    },
    "storytelling": {
        "structure": "One person shares an extended narrative with occasional responses",
        "suitable_for": "Sharing experiences, teaching moments, or entertainment",
        "typical_length": "Extended turns from storyteller with brief listener responses",
    },
    "problem_solving": {
        "structure": "Focused exchange to identify and resolve an issue",
        "suitable_for": "Work discussions, relationship conflicts, or practical challenges",
        "typical_length": "10-20 exchanges with solution-oriented progression",
    },
    "casual_chat": {
        "structure": "Loosely connected topics with fluid transitions and lighter content",
        "suitable_for": "Social bonding, passing time, or maintaining connections",
        "typical_length": "Variable, often 5-15 brief exchanges",
    },
    "debate_format": {
        "structure": "Presentation of opposing viewpoints with structured arguments",
        "suitable_for": "Controversial topics, decision-making, or intellectual exercise",
        "typical_length": "10-30 exchanges with developed positions",
    },
    "teaching_dialogue": {
        "structure": "Knowledge transfer with explanations, questions, and confirmations",
        "suitable_for": "Educational contexts, mentoring, or skill development",
        "typical_length": "10-25 exchanges with explanatory content",
    },
    "emotional_support": {
        "structure": "One person expresses difficulties, other responds with empathy",
        "suitable_for": "Personal struggles, seeking comfort, or relationship building",
        "typical_length": "10-20 exchanges with emotional content",
    },
}

# Relationship dynamics between conversation participants
RELATIONSHIP_TYPES = {
    "strangers": {
        "familiarity": "None or minimal",
        "typical_patterns": [
            "politeness",
            "boundary maintenance",
            "limited self-disclosure",
            "information seeking",
        ],
        "power_dynamic": "Often neutral or situational",
    },
    "acquaintances": {
        "familiarity": "Limited, surface-level",
        "typical_patterns": [
            "small talk",
            "exploring common interests",
            "tentative self-disclosure",
            "establishing rapport",
        ],
        "power_dynamic": "Usually balanced or contextual",
    },
    "friends": {
        "familiarity": "Moderate to high",
        "typical_patterns": [
            "inside jokes",
            "direct communication",
            "personal disclosure",
            "emotional support",
        ],
        "power_dynamic": "Generally egalitarian with established roles",
    },
    "close_friends": {
        "familiarity": "High with shared history",
        "typical_patterns": [
            "high trust",
            "emotional intimacy",
            "honest feedback",
            "deep discussions",
        ],
        "power_dynamic": "Balanced with understood boundaries",
    },
    "romantic_partners": {
        "familiarity": "High with intimate knowledge",
        "typical_patterns": [
            "affection",
            "future planning",
            "domestic discussions",
            "emotional intimacy",
        ],
        "power_dynamic": "Complex with negotiated domains",
    },
    "family_members": {
        "familiarity": "High with long history",
        "typical_patterns": [
            "established patterns",
            "familial references",
            "shared history",
            "role expectations",
        ],
        "power_dynamic": "Often hierarchical but evolving",
    },
    "colleagues": {
        "familiarity": "Professional with varying personal elements",
        "typical_patterns": [
            "work focus",
            "professional boundaries",
            "information exchange",
            "collaborative language",
        ],
        "power_dynamic": "Organizational hierarchy or peer-based",
    },
    "mentor_mentee": {
        "familiarity": "Professional with developmental focus",
        "typical_patterns": ["guidance", "questions", "feedback", "growth discussions"],
        "power_dynamic": "Asymmetrical but supportive",
    },
    "service_provider_client": {
        "familiarity": "Limited, role-based",
        "typical_patterns": [
            "service focus",
            "need assessment",
            "solution offering",
            "professional boundaries",
        ],
        "power_dynamic": "Service-oriented with customer emphasis",
    },
    "authority_subordinate": {
        "familiarity": "Professional with clear hierarchy",
        "typical_patterns": ["direction giving", "reporting", "evaluation", "formal communication"],
        "power_dynamic": "Clearly asymmetrical",
    },
}

# Communication mediums that shape conversation style
COMMUNICATION_MEDIUMS = {
    "face_to_face": {
        "characteristics": [
            "nonverbal cues",
            "immediate feedback",
            "full attention",
            "natural flow",
        ],
        "typical_effects": "Richer exchange with social and emotional elements",
    },
    "phone_call": {
        "characteristics": [
            "voice cues only",
            "real-time",
            "no visual cues",
            "potential distractions",
        ],
        "typical_effects": "More explicit communication, less nonverbal nuance",
    },
    "video_call": {
        "characteristics": [
            "partial visual cues",
            "technology mediation",
            "shared virtual space",
            "potential technical issues",
        ],
        "typical_effects": "Similar to face-to-face but with some limitations and awkwardness",
    },
    "text_messaging": {
        "characteristics": ["written only", "asynchronous", "brevity", "emoji/abbreviations"],
        "typical_effects": "Concise, potentially ambiguous, time for composition",
    },
    "email": {
        "characteristics": ["longer form", "asynchronous", "more formal", "permanent record"],
        "typical_effects": "More structured, thought-out communication with less spontaneity",
    },
    "social_media": {
        "characteristics": [
            "public or semi-public",
            "audience awareness",
            "platform conventions",
            "multimedia elements",
        ],
        "typical_effects": "Performance-oriented with audience consideration",
    },
    "written_letters": {
        "characteristics": [
            "high effort",
            "significant delay",
            "thoughtful composition",
            "permanent",
        ],
        "typical_effects": "Deliberate, meaningful, often deeper communication",
    },
    "group_chat": {
        "characteristics": [
            "multiple participants",
            "overlapping threads",
            "variable attention",
            "group dynamics",
        ],
        "typical_effects": "More chaotic, less in-depth, social positioning",
    },
}

# Emotional tones that can be applied to conversations
EMOTIONAL_TONES = {
    "neutral": ["balanced", "objective", "even", "moderate", "calm"],
    "positive": ["upbeat", "optimistic", "enthusiastic", "warm", "appreciative"],
    "negative": ["pessimistic", "critical", "frustrated", "disappointed", "concerned"],
    "tense": ["anxious", "stressed", "uncomfortable", "cautious", "on-edge"],
    "relaxed": ["comfortable", "easy-going", "laid-back", "content", "peaceful"],
    "formal": ["professional", "proper", "distant", "structured", "ceremonial"],
    "informal": ["casual", "familiar", "relaxed", "conversational", "everyday"],
    "humorous": ["playful", "witty", "joking", "light-hearted", "amusing"],
    "serious": ["earnest", "grave", "solemn", "important", "weighty"],
    "intimate": ["close", "personal", "revealing", "vulnerable", "connected"],
}

# Conversation topics from different domains
CONVERSATION_TOPICS = {
    "personal": [
        "childhood memories",
        "family relationships",
        "personal goals",
        "life changes",
        "hobbies and interests",
        "personal challenges",
        "values and beliefs",
        "daily routines",
        "living situation",
        "personal achievements",
        "health and wellness",
        "future aspirations",
    ],
    "social": [
        "mutual friends",
        "recent events",
        "social gatherings",
        "community issues",
        "social media",
        "cultural trends",
        "social norms",
        "relationships",
        "dating experiences",
        "group activities",
        "social movements",
        "networking",
    ],
    "professional": [
        "career goals",
        "workplace dynamics",
        "job responsibilities",
        "industry trends",
        "work challenges",
        "professional development",
        "work-life balance",
        "company culture",
        "job satisfaction",
        "team projects",
        "professional achievements",
        "business strategies",
    ],
    "educational": [
        "learning experiences",
        "academic interests",
        "educational background",
        "teaching methods",
        "study strategies",
        "educational systems",
        "knowledge acquisition",
        "research interests",
        "academic challenges",
        "intellectual discussions",
        "educational resources",
        "knowledge sharing",
    ],
    "leisure": [
        "entertainment preferences",
        "travel experiences",
        "sports and activities",
        "creative pursuits",
        "relaxation techniques",
        "games and recreation",
        "music and arts",
        "dining experiences",
        "media consumption",
        "outdoor activities",
        "collecting hobbies",
        "leisure time management",
    ],
    "current_events": [
        "news stories",
        "political developments",
        "societal changes",
        "technological advancements",
        "environmental issues",
        "economic trends",
        "cultural events",
        "global affairs",
        "local news",
        "industry updates",
        "social justice issues",
        "current debates",
    ],
    "philosophical": [
        "meaning and purpose",
        "ethical questions",
        "human nature",
        "societal structures",
        "philosophical traditions",
        "moral dilemmas",
        "existence and reality",
        "consciousness",
        "truth and knowledge",
        "faith and spirituality",
        "justice and fairness",
        "free will",
    ],
    "practical": [
        "problem-solving",
        "advice seeking",
        "resource sharing",
        "planning and coordination",
        "decision-making",
        "technical questions",
        "practical tips",
        "processes and methods",
        "tool recommendations",
        "efficiency strategies",
        "practical challenges",
        "implementation details",
    ],
}


# Function to generate conversation parameters based on desired personality traits
def generate_conversation_parameters(
    primary_trait=None, secondary_trait=None, excluded_traits=None
):
    """
    Generate a set of conversation parameters suitable for creating synthetic dialogue
    that exhibits specified personality traits.

    Args:
        primary_trait (str, optional): Main personality trait to emphasize
        secondary_trait (str, optional): Secondary personality trait to include
        excluded_traits (list, optional): Traits to specifically avoid

    Returns:
        dict: Configuration for generating a personality-exhibiting conversation
    """
    import random

    # Default to random selection if traits not specified
    # TODO: Implement trait extraction from persona file
    # Select scenario and approach
    scenario = random.choice(list(CONVERSATION_SCENARIOS.keys()))
    approach = random.choice(list(CONVERSATION_APPROACHES.keys()))
    relationship = random.choice(list(RELATIONSHIP_TYPES.keys()))
    medium = random.choice(list(COMMUNICATION_MEDIUMS.keys()))

    # Select emotion tone with some bias toward compatibility with traits
    # TODO: Implement code to build tone weights based on persona, scenario, or relationship
    tone_weights = {}

    tones = list(tone_weights.keys())
    weights = list(tone_weights.values())
    emotional_tone = random.choices(tones, weights=weights, k=1)[0]

    # Select topic domain with some bias toward compatibility with scenario
    scenario_info = CONVERSATION_SCENARIOS[scenario]
    if "work" in scenario or "job" in scenario or "project" in scenario:
        topic_domain_weights = {
            "professional": 0.5,
            "practical": 0.2,
            "social": 0.1,
            "current_events": 0.1,
            "personal": 0.1,
        }
    elif "friend" in scenario or "date" in scenario or "party" in scenario:
        topic_domain_weights = {
            "personal": 0.4,
            "social": 0.3,
            "leisure": 0.2,
            "current_events": 0.1,
        }
    elif "family" in scenario:
        topic_domain_weights = {
            "personal": 0.5,
            "social": 0.2,
            "practical": 0.1,
            "leisure": 0.1,
            "current_events": 0.1,
        }
    else:
        # Random selection
        topic_domains = list(CONVERSATION_TOPICS.keys())
        topic_domain_weights = {domain: 1 / len(topic_domains) for domain in topic_domains}

    domains = list(topic_domain_weights.keys())
    domain_weights = list(topic_domain_weights.values())
    topic_domain = random.choices(domains, weights=domain_weights, k=1)[0]

    # Select specific topic from domain
    specific_topic = random.choice(CONVERSATION_TOPICS[topic_domain])

    # Define personality expression intensity (how strongly to show the trait)
    intensity = random.choice(["subtle", "moderate", "strong", "very_strong"])

    # Compile the configuration
    config = {
        # TODO: Implement personality extraction from persona file
        "personality": {
            "primary_trait": primary_trait,
            "primary_attributes": "",
            "secondary_trait": secondary_trait,
            "secondary_attributes": "",
            "expression_intensity": intensity,
        },
        "conversation_setup": {
            "scenario": scenario,
            "scenario_details": scenario_info,
            "relationship_type": relationship,
            "relationship_details": RELATIONSHIP_TYPES[relationship],
            "communication_medium": medium,
            "medium_details": COMMUNICATION_MEDIUMS[medium],
        },
        "conversation_structure": {
            "approach": approach,
            "approach_details": CONVERSATION_APPROACHES[approach],
            "emotional_tone": emotional_tone,
            "tone_attributes": EMOTIONAL_TONES[emotional_tone],
            "topic_domain": topic_domain,
            "specific_topic": specific_topic,
        },
    }

    return config


# Example prompt builder to create LLM prompts from the configuration
def create_generation_prompt(config):
    """
    Create a detailed prompt for an LLM to generate a conversation based on the configuration.

    Args:
        config (dict): Configuration from generate_conversation_parameters()

    Returns:
        str: A prompt ready to send to an LLM for conversation generation
    """
    personality = config["personality"]
    setup = config["conversation_setup"]
    structure = config["conversation_structure"]
    guidelines = config["generation_guidelines"]

    # Build the prompt
    prompt = f"""
Create a realistic conversation between Speaker 1 and Speaker 2 with the following specifications:

PERSONALITY TRAITS:
Speaker {guidelines['show_trait_in_speaker']} exhibits a {personality['expression_intensity']} {personality['primary_trait']} personality,
characterized by these attributes: {', '.join(personality['primary_attributes'])}.
"""

    if personality["secondary_trait"]:
        prompt += f"\nThey also show some {personality['secondary_trait']} tendencies, with these attributes: {', '.join(personality['secondary_attributes'])}.\n"

    prompt += f"""
CONVERSATION SETUP:
- Scenario: {setup['scenario'].replace('_', ' ').title()} - {setup['scenario_details']['context']}
- Relationship: {setup['relationship_type'].replace('_', ' ').title()} - {setup['relationship_details']['familiarity']}
- Communication Medium: {setup['communication_medium'].replace('_', ' ').title()} - {setup['medium_details']['characteristics'][0]}

CONVERSATION DETAILS:
- Structure: {structure['approach'].replace('_', ' ').title()} - {structure['approach_details']['structure']}
- Emotional Tone: {structure['emotional_tone'].title()} ({', '.join(structure['tone_attributes'][:3])})
- Topic: {structure['specific_topic'].title()} (in the domain of {structure['topic_domain'].replace('_', ' ')})
- Length: Approximately {structure['num_turns']} total exchanges

The conversation should feel natural and realistic while clearly showcasing the specified personality traits.
Avoid explicitly mentioning or labeling the personality traits in the conversation itself.

Format the conversation as:
Speaker 1: [Message]
Speaker 2: [Message]
...and so on.
"""

    return prompt


# Example usage
if __name__ == "__main__":
    # Generate conversation parameters for an extroverted personality
    config = generate_conversation_parameters(
        primary_trait="extroverted", secondary_trait="agreeable"
    )

    # Create a prompt for an LLM
    prompt = create_generation_prompt(config)

    print("Example LLM Prompt for Conversation Generation:")
    print(prompt)

    # To generate multiple diverse conversations:
    # conversations = []
    # for _ in range(5):
    #     config = generate_conversation_parameters()
    #     prompt = create_generation_prompt(config)
    #     # Send prompt to LLM and collect the response
    #     # conversations.append((config, llm_response))
