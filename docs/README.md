# Документация проекта

Этот каталог хранит проектные решения, архитектуру, правила разработки и backlog перехода на новую архитектуру.

## Основные документы

- [architecture.md](architecture.md) - целевая архитектура проекта.
- [backlog.md](backlog.md) - backlog архитектурного перехода и дальнейшей разработки.
- [development.md](development.md) - правила локальной разработки.
- [deployment.md](deployment.md) - план деплоя на VPS.
- [telegram-mini-app.md](telegram-mini-app.md) - особенности Telegram Web App / Mini App.

## Архитектурные решения

Решения фиксируются в формате ADR в каталоге [decisions](decisions):

- [0001-project-architecture.md](decisions/0001-project-architecture.md) - модульный монорепозиторий с независимыми приложениями.
- [0002-auth-strategy.md](decisions/0002-auth-strategy.md) - стратегия авторизации.
- [0003-frontend-stack.md](decisions/0003-frontend-stack.md) - React/Vite SPA.
- [0004-background-workers.md](decisions/0004-background-workers.md) - фоновые задачи через worker.

