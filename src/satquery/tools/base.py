from abc import ABC, abstractmethod
from typing import Dict, Any, List
from PIL import Image

class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, images: List[Image.Image], query: str, **kwargs) -> Dict[str, Any]:
        """Executes the tool logic and returns a structured result dictionary."""
        pass
