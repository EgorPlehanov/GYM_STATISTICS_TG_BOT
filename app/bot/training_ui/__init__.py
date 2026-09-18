"""Общий Telegram UI-слой сценария тренировки."""

from .lock import TrainingFlowLockMiddleware
from .renderer import TrainingView, render_training_view
from .service import (
    TrainingTransitionResult,
    delete_training_message,
    is_current_training_callback,
    replace_after_backend,
    replace_training_markup,
    show_or_recover_target,
    start_training_screen,
    transition_training_screen,
)

__all__ = [
    "TrainingTransitionResult",
    "TrainingFlowLockMiddleware",
    "TrainingView",
    "delete_training_message",
    "is_current_training_callback",
    "render_training_view",
    "replace_after_backend",
    "replace_training_markup",
    "show_or_recover_target",
    "start_training_screen",
    "transition_training_screen",
]
