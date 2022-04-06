import typing
from typing import Any, Optional, Text, Dict, List, Type
import re

from rasa.nlu.components import Component
from rasa.nlu.config import RasaNLUModelConfig
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.constants import TEXT

if typing.TYPE_CHECKING:
    from rasa.nlu.model import Metadata


class EnzoPreprocessor(Component):
    def process(self, message: Message, **kwargs: Any) -> None:
        txt = message.get(TEXT)
        if txt is None:
            return
        try:
            # remove all chars not in list; condense multiple spaces to one
            # out = re.sub(r"[^A-Za-z0-9 \#\@\$\£\+\-\_]", " ", txt)
            out = re.sub(r"[,;.]", " ", txt)
            out = re.sub("\s\s+", " ", out)
            message.set(TEXT, out)
        except:
            print(f"error found with text\n{txt}")

    @classmethod
    def load(
        cls,
        meta: Dict[Text, Any],
        model_dir: Text,
        model_metadata: Optional["Metadata"] = None,
        cached_component: Optional["Component"] = None,
        **kwargs: Any,
    ) -> "Component":
        """Load this component from file."""

        if cached_component:
            return cached_component
        else:
            return cls(meta)
