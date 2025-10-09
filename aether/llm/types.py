from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import TypeAlias

# Message types
MessageRole = Literal["system", "user", "assistant", "tool"]

Message: TypeAlias = Dict[str, Any]
Messages: TypeAlias = List[Message]
