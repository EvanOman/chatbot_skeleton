from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"