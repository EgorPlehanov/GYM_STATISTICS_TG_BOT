"""Точка входа для конфигурации приложения.

Сейчас реальные настройки находятся в старом модуле `config_reader`.
Они будут перенесены сюда на этапе рефакторинга backend core.
"""

from config_reader import Settings, config

__all__ = ["Settings", "config"]
