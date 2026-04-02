# Учебный проект: REST API объявлений на FastAPI (Netology, части 1–2)

Проект закрывает два домашних задания:

- [3.1-fast-api-1](https://github.com/netology-code/py-homeworks-web/tree/new/3.1-fast-api-1) — объявления, CRUD, поиск, Docker (`Docs/readme_netology_3.1_fast_api_1.md`).
- [3.2-fast-api-2](https://github.com/netology-code/py-homeworks-web/tree/new/3.2-fast-api-2) — вход по JWT (48 ч), пользователи `user` / `admin`, матрица прав, 401/403 (`Docs/readme_netology_3.2_fast_api_2.md`).

Код в `src/`, автотесты в `src/Tests/`. Это **FastAPI**-проект (не Django).

## Проверка соответствия заданию 3.1 (объявления)

| Требование | Реализация |
|------------|------------|
| Поля объявления | `title`, `description`, `price`, `author` (в ответе), `created_at` (сервер), внутри — `owner_user_id` для прав из части 2 |
| `POST /advertisement` | **201**, только с JWT (часть 2); автор в ответе по умолчанию — логин создателя |
| `PATCH` / `DELETE` / `GET` по id, поиск `GET /advertisement` | Как в части 1; изменение/удаление — с JWT, владелец или `admin` |
| Докеризация | `Dockerfile`, `docker-compose.yml` |

Ответ поиска: `items`, `total`.

## Проверка соответствия заданию 3.2 (авторизация и пользователи)

| Требование | Реализация |
|------------|------------|
| `POST /login` | JSON `username`, `password` → `access_token`, `token_type`; неверная пара — **401** |
| Срок токена | `ACCESS_TOKEN_EXPIRE_HOURS` (по умолчанию **48**) |
| Пользователи | `GET/POST/PATCH/DELETE /user/...`, роли **`user`** и **`admin`** |
| Гость | `POST /user`, `GET /user/{id}`, `GET /advertisement`, `GET /advertisement/{id}` |
| Роль `user` | то же + `PATCH/DELETE` **себя** + `POST/PATCH/DELETE` **своих** объявлений |
| Роль `admin` | любые операции над пользователями и объявлениями |
| Недостаточно прав | **403** |
| Создание `admin` без существующего admin | **403**; первый администратор — через переменные **`BOOTSTRAP_ADMIN_*`** или вручную после временной правки (в тестах — сид в `conftest`) |

Заголовок для защищённых методов: `Authorization: Bearer <access_token>`.

## Результаты последней проверки (2026-04-02)

- **Автотесты**: `pytest` — **13** тестов, все успешно (`src/Tests/`): объявления (в т. ч. без токена 401, чужое объявление 403), вход 401, создание `admin` без прав 403, сценарии `admin`, каскадное удаление объявлений при удалении пользователя.
- **Соответствие ТЗ**: пункты таблиц выше сверены с кодом маршрутов в `src/router_*.py` и с текстами в `Docs/readme_netology_3.1_fast_api_1.md`, `Docs/readme_netology_3.2_fast_api_2.md`.
- **Ручная проверка**: после `uvicorn src.main:app` — `http://127.0.0.1:8000/docs` (регистрация → логин → копирование токена → вызовы с `Authorize`).
- **Docker**: образ собирается `docker compose build`; для запуска нужен работающий демон Docker на машине.

**Публичный репозиторий:** [github.com/OrionFLASH/Netology_DZ_Py_REST_API_on_FastApi_part1](https://github.com/OrionFLASH/Netology_DZ_Py_REST_API_on_FastApi_part1).

## Структура проекта

| Путь | Назначение |
|------|------------|
| `src/main.py` | Приложение, роутеры, lifespan (логи, опциональный bootstrap-админ) |
| `src/config.py` | Настройки, JWT, bootstrap |
| `src/deps.py` | Зависимости: хранилища, `CurrentUser`, опциональный/обязательный JWT |
| `src/jwt_service.py` | Выдача и проверка JWT |
| `src/passwords.py` | bcrypt: хеш и проверка пароля |
| `src/user_storage.py` | In-memory пользователи |
| `src/storage.py` | In-memory объявления, каскадное удаление по владельцу |
| `src/schemas.py` | Pydantic-модели |
| `src/router_login.py` | `POST /login` |
| `src/router_user.py` | `/user` |
| `src/router_advertisement.py` | `/advertisement` |
| `src/logging_setup.py` | Логи в `log/` |
| `src/Tests/` | Pytest |
| `Docs/` | Тексты заданий |

## Описание решения

- **Объявления** хранятся в памяти с полем **`owner_user_id`**. Поле **`author`** в API — отображаемая строка (по умолчанию логин создателя; администратор может задать при создании).
- **Пароли** — только в виде bcrypt-хешей. **JWT** (PyJWT), роль при проверке берётся из актуальной записи пользователя.
- Удаление пользователя **удаляет его объявления** из in-memory хранилища.
- **Первый администратор в проде**: задайте в `.env` `BOOTSTRAP_ADMIN_USERNAME` и `BOOTSTRAP_ADMIN_PASSWORD` (однократное создание при старте, если логин ещё не занят).

## Переменные окружения

См. `.env.example`:

| Переменная | Назначение |
|------------|------------|
| `APP_HOST`, `APP_PORT`, `LOG_LEVEL` | Сервер и логи в консоль |
| `JWT_SECRET` | Секрет подписи JWT |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Срок жизни токена (часы), по заданию 48 |
| `BOOTSTRAP_ADMIN_USERNAME`, `BOOTSTRAP_ADMIN_PASSWORD` | Опционально: создать admin при старте |

## Установка и запуск (локально)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Документация API: `http://127.0.0.1:8000/docs`.

## Запуск в Docker

```bash
docker compose up --build
```

Сервис: `http://127.0.0.1:8000`.

## Тестирование

```bash
pytest
```

В `conftest` создаётся учётная запись **`seed_admin` / `seed_secret`**, чтобы тестировать сценарии с `admin` без обхода правил API.

## Примеры `curl`

```bash
# Регистрация и вход
curl -s -X POST http://127.0.0.1:8000/user -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}'
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}' | jq -r .access_token)

# Создание объявления (нужен Bearer)
curl -s -X POST http://127.0.0.1:8000/advertisement \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Книга","description":"Учебник","price":500}'

# Поиск без токена
curl -s "http://127.0.0.1:8000/advertisement?title=книга"
```

## Список основных сущностей кода

| Имя | Назначение |
|-----|------------|
| `get_settings`, `Settings` | Конфигурация приложения |
| `get_advertisement_store`, `get_user_store` | Зависимости хранилищ |
| `get_current_user_optional`, `require_current_user` | JWT: опционально / обязательно |
| `create_access_token`, `decode_access_token` | JWT |
| `hash_password`, `verify_password` | Пароли |
| `UserStore`, `UserRole`, `UserRecord` | Пользователи |
| `AdvertisementStore`, `AdvertisementRecord` | Объявления |
| `ensure_bootstrap_admin` | Стартовый admin из `.env` |
| Роуты в `router_*.py` | HTTP API |

## История версий

| Версия | Изменения |
|--------|-----------|
| 1.0.0–1.0.2 | Часть 1: CRUD объявлений, поиск, Docker, логи, документация, проверки. |
| 2.0.0 | Часть 2: `POST /login`, JWT 48 ч, пользователи и роли, матрица прав 401/403, владелец объявлений, каскад при удалении пользователя, тесты, обновление README и `Docs`. |
| 2.0.1 | Документация: зафиксированы результаты проверки (`pytest`, ручные шаги, Docker), ссылка на GitHub в README. |
