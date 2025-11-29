# agents_core/observer.py
from typing import Dict, Any

from backend.utils import get_state


def observe() -> Dict[str, Any]:
    """
    Reads the full financial state from backend utils.
    """
    return get_state()
