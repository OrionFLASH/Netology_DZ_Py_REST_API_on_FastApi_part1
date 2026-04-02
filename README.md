# Учебный проект: REST API объявлений на FastAPI (Netology, часть 1)

Проект выполняет домашнее задание по лекции «Создание REST API на FastAPI» ([исходная формулировка](https://github.com/netology-code/py-homeworks-web/tree/new/3.1-fast-api-1)) — сервис объявлений купли/продажи без аутентификации, с докеризацией.

В репозитории **одна задача** (FastAPI, не Django): исходный текст задания и материалы лежат в каталоге `Docs/`, код — в `src/`, автотесты — в `src/Tests/`.

## Проверка соответствия заданию Netology

Формулировка: [3.1-fast-api-1](https://github.com/netology-code/py-homeworks-web/tree/new/3.1-fast-api-1) (файл в репозитории: `Docs/readme_netology_3.1_fast_api_1.md`).

| Требование | Реализация |
|------------|------------|
| Поле «заголовок» | JSON-поле `title` в создании/обновлении/ответах |
| Поле «описание» | `description` |
| Поле «цена» | `price` (число, неотрицательное) |
| Поле «автор» | `author` |
| Поле «дата создания» | `created_at`: задаётся при `POST`, не меняется при `PATCH`, в UTC |
| `POST /advertisement` | Создание, ответ **201**, тело — объявление с `id` и `created_at` |
| `PATCH /advertisement/{advertisement_id}` | Частичное обновление, ответ **200** или **404** |
| `DELETE /advertisement/{advertisement_id}` | Удаление, ответ **204** или **404** |
| `GET /advertisement/{advertisement_id}` | Одна запись, **200** или **404** |
| `GET /advertisement?{query_string}` | Поиск по полям (см. ниже); без параметров — полный список |
| Без авторизации | Заголовки авторизации не проверяются |
| Докеризация | `Dockerfile`, `docker-compose.yml` в корне репозитория |

Ответ поиска `GET /advertisement`: объект JSON с полями `items` (массив объявлений в том же формате, что и при получении по id) и `total` (число элементов).

## Результаты проверки работы

- **Автотесты (`pytest`)**: все тесты в `src/Tests/` проходят (создание, чтение, изменение, удаление, поиск по query, список без фильтров).
- **Ручная проверка**: после запуска `uvicorn` откройте `http://127.0.0.1:8000/docs` и выполните цепочку POST → GET по id → PATCH → GET с параметрами → DELETE.
- **Docker**: сборка и запуск — `docker compose up --build`. Убедитесь, что демон Docker запущен (на macOS обычно Docker Desktop); если сокет недоступен, команда сообщит об ошибке подключения к Docker API.

## Структура проекта

| Путь | Назначение |
|------|------------|
| `src/main.py` | Создание приложения FastAPI, подключение роутера, жизненный цикл (логирование при старте) |
| `src/config.py` | Настройки из переменных окружения и `.env` |
| `src/logging_setup.py` | Файловые логи `INFO` и `DEBUG` в каталоге `log/` |
| `src/schemas.py` | Pydantic-модели запросов и ответов |
| `src/storage.py` | In-memory хранилище объявлений |
| `src/router_advertisement.py` | Маршруты `/advertisement` |
| `src/Tests/` | Pytest-тесты API |
| `Docs/` | Текст задания Netology |
| `Dockerfile`, `docker-compose.yml` | Сборка и запуск в контейнере |

## Техническое задание (кратко)

Поля объявления: заголовок, описание, цена, автор, дата создания (назначается сервером).

Эндпоинты:

- `POST /advertisement` — создание
- `PATCH /advertisement/{advertisement_id}` — обновление
- `DELETE /advertisement/{advertisement_id}` — удаление
- `GET /advertisement/{advertisement_id}` — получение по id
- `GET /advertisement?...` — поиск по полям (query string)

## Описание решения

- Данные хранятся **в оперативной памяти** процесса (`AdvertisementStore`), с блокировкой `threading.RLock` для безопасного доступа из нескольких потоков uvicorn.
- Идентификатор объявления — **UUID** в виде строки.
- Дата создания — **UTC** (`datetime` с timezone).
- Поиск: параметры query объединяются по логике **И**. Для строк используется **подстрока без учёта регистра**. Доступные параметры: `title`, `description`, `author`, `price_min`, `price_max`, `created_from`, `created_to` (даты в формате ISO 8601). Без параметров возвращаются все объявления.
- Логи: в `log/` создаются файлы по шаблону `INFO_advertisement_api_ГГГГММДД_ЧЧ.log` и `DEBUG_advertisement_api_ГГГГММДД_ЧЧ.log`; строки `DEBUG` в файле DEBUG соответствуют требуемому формату с указанием класса и функции.

## Переменные окружения

Задаются в `.env` (шаблон — `.env.example`):

| Переменная | Назначение | Пример |
|------------|------------|--------|
| `APP_HOST` | Хост uvicorn | `0.0.0.0` |
| `APP_PORT` | Порт (для локального запуска скриптом; в Docker порт задаётся образом) | `8000` |
| `LOG_LEVEL` | Уровень логов в консоль | `INFO` |

## Установка и запуск (локально)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Интерактивная документация OpenAPI: `http://127.0.0.1:8000/docs`.

## Запуск в Docker

```bash
docker compose up --build
```

Сервис: `http://127.0.0.1:8000` (эндпоинты те же).

## Тестирование

```bash
source .venv/bin/activate
pytest
```

Ожидаемое поведение: все тесты проходят; вручную можно проверить сценарии создания → чтение → изменение → удаление и выборку `GET /advertisement?author=...` через Swagger или `curl`.

### Примеры `curl`

```bash
curl -s -X POST http://127.0.0.1:8000/advertisement \
  -H "Content-Type: application/json" \
  -d '{"title":"Книга","description":"Учебник Python","price":500,"author":"Анна"}'

curl -s "http://127.0.0.1:8000/advertisement?title=книга"
```

## Список основных сущностей кода

| Имя | Тип | Назначение |
|-----|-----|------------|
| `get_settings` | функция | Возвращает объект настроек `Settings` |
| `Settings` | класс | Поля `app_host`, `app_port`, `log_level` |
| `setup_logging` | функция | Настраивает корневой логгер, файлы в `log/` |
| `log_debug` | функция | Запись в DEBUG-файл в требуемом формате |
| `AdvertisementCreate` | Pydantic-модель | Тело `POST /advertisement` |
| `AdvertisementUpdate` | Pydantic-модель | Тело `PATCH` (все поля опциональны) |
| `AdvertisementRead` | Pydantic-модель | Ответ с полями объявления |
| `AdvertisementListResponse` | Pydantic-модель | Ответ поиска: `items`, `total` |
| `AdvertisementRecord` | dataclass | Внутренняя запись в хранилище |
| `AdvertisementStore` | класс | `create`, `get`, `update`, `delete`, `search` |
| `store` | экземпляр | Глобальное хранилище процесса (в тестах подменяется) |
| `create_advertisement` | endpoint | `POST /advertisement` |
| `patch_advertisement` | endpoint | `PATCH /advertisement/{id}` |
| `delete_advertisement` | endpoint | `DELETE /advertisement/{id}` |
| `get_advertisement` | endpoint | `GET /advertisement/{id}` |
| `search_advertisements` | endpoint | `GET /advertisement` |
| `app` | FastAPI | Корневое приложение |

## История версий

| Версия | Изменения |
|--------|-----------|
| 1.0.0 | Первоначальная реализация задания Netology 3.1 FastAPI часть 1: CRUD, поиск по query, Docker, логирование, pytest, документация. |
| 1.0.1 | Удалён неиспользуемый метод из модуля хранилища. |
| 1.0.2 | Добавлены в README разделы проверки соответствия заданию и результатов проверки (тесты, Swagger, Docker). |
