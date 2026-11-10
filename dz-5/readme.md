# Лабораторная работа: «Модульная банковская система на Python»

## Цель работы

Спроектировать и реализовать на Python банковскую систему, в которой каждая функция вынесена в отдельный модуль (пакет), а изменение любого модуля не требует правок в остальных.

В ходе работы нужно освоить на практике:

- слабую связанность;
- высокую связность;
- плагинную архитектуру;
- событийное взаимодействие.

## Теоретическая часть

| Принцип | Суть | Как проявляется в работе |
|---------|------|--------------------------|
| SRP | Один модуль — одна причина для изменения | `deposits` отвечает только за пополнение, `fees` — только за комиссии |
| DIP | Зависимость от абстракций, а не от реализаций | Модули общаются через `typing.Protocol` / `ABC` |
| Слабая связанность | `core` не знает о конкретных модулях | Модули регистрируются через `config.toml` / entry points |
| Событийная шина | Публикация и подписка вместо прямых вызовов | `deposits` публикует `money.deposited`, `notifications` его слушает |

> Главная идея: `core` знает только про `BankModule` и `ModuleContext`. Всё остальное — сменные плагины.

## Архитектура

### Общая схема модулей
```mermaid
flowchart TB
    subgraph HOST["host"]
        MAIN["main.py&lt;br/&gt;точка входа"]
        CFG[("config.toml")]
    end

    subgraph CORE["core (ядро)"]
        LOADER["loader.py&lt;br/&gt;загрузка через entry_points"]
        MOD["module.py&lt;br/&gt;BankModule, ModuleContext"]
        BUS["events.py&lt;br/&gt;EventBus"]
        REG["Registry&lt;br/&gt;сервисы по протоколам"]
        PROTO["protocols.py&lt;br/&gt;AccountsAPI, Repository, ..."]
        CLI["cli.py&lt;br/&gt;CommandRegistry"]
    end

    subgraph BASE["Базовые модули"]
        AUTH["auth"]
        ACC["accounts"]
        DEP["deposits"]
        WD["withdrawals"]
        TR["transfers"]
        REP["reports"]
    end

    subgraph INFRA["Инфраструктурные модули"]
        PERS["persistence&lt;br/&gt;memory / json / sqlite"]
        NOTIF["notifications&lt;br/&gt;log / email / sms"]
    end

    subgraph EXTRA["Дополнительные модули (минимум 4)"]
        FEES["fees"]
        LIM["limits"]
        FRAUD["fraud_control"]
        BONUS["bonus_points"]
        OTHER["currency, savings, credits,&lt;br/&gt;scheduler, audit_log,&lt;br/&gt;admin, analytics"]
    end

    MAIN --&gt; LOADER
    CFG -. "список модулей&lt;br/&gt;и настройки" .-&gt; LOADER
    LOADER -- "создаёт ModuleContext,&lt;br/&gt;вызывает initialize()" --&gt; BASE
    LOADER -- "initialize()" --&gt; INFRA
    LOADER -- "initialize()" --&gt; EXTRA

    BASE &lt;-- "publish / subscribe" --&gt; BUS
    INFRA &lt;-- "subscribe" --&gt; BUS
    EXTRA &lt;-- "publish / subscribe" --&gt; BUS

    BASE -. "получает сервисы&lt;br/&gt;по протоколу" .-&gt; REG
    EXTRA -. "получает сервисы&lt;br/&gt;по протоколу" .-&gt; REG
    PERS -- "регистрирует Repository" --&gt; REG
    ACC -- "регистрирует AccountsAPI" --&gt; REG

    BASE -. "реализует" .-&gt; PROTO
    BASE -- "register_commands()" --&gt; CLI
    EXTRA -- "register_commands()" --&gt; CLI
```

Правила, которые видны на схеме:

- Стрелки идут только к `core` и от `core`. Прямых связей между бизнес-модулями нет.
- `core` ничего не импортирует из `bank_modules`.
- Модули получают чужие сервисы только через `Registry` по протоколу, например `ctx.registry.get(AccountsAPI)`.

### Жизненный цикл загрузки модулей
```mermaid
sequenceDiagram
    autonumber
    participant M as host/main.py
    participant L as core.loader
    participant EP as entry_points("bank.modules")
    participant X as BankModule (каждый)
    participant C as CommandRegistry

    M-&gt;&gt;L: load(config.toml)
    L-&gt;&gt;EP: найти все модули группы bank.modules
    EP--&gt;&gt;L: список классов
    L-&gt;&gt;L: отфильтровать по modules.enabled
    loop для каждого включённого модуля
        L-&gt;&gt;X: initialize(ctx)
        X-&gt;&gt;X: подписка на события, регистрация сервисов
        L-&gt;&gt;X: register_commands(cli)
        X-&gt;&gt;C: add("deposit", handler)
    end
    M-&gt;&gt;C: run() — интерактивный цикл
    Note over M,X: при выходе: shutdown() у всех модулей
```

### Пример: перевод между счетами
```mermaid
sequenceDiagram
    autonumber
    actor U as Клиент
    participant T as transfers
    participant B as EventBus
    participant LIM as limits
    participant FR as fraud_control
    participant F as fees
    participant A as accounts (через AccountsAPI)
    participant N as notifications
    participant R as reports / audit_log

    U-&gt;&gt;T: transfer A1 → A2, 5000
    T-&gt;&gt;B: publish("transfer.requested")
    B-&gt;&gt;LIM: проверка лимитов
    B-&gt;&gt;FR: проверка на подозрительность
    alt операция отклонена
        LIM--&gt;&gt;T: raise OperationRejected
        T-&gt;&gt;B: publish("transfer.rejected")
        B-&gt;&gt;N: уведомление об отказе
    else операция разрешена
        B-&gt;&gt;F: расчёт комиссии
        F-&gt;&gt;B: publish("fee.charged")
        T-&gt;&gt;A: debit(A1), credit(A2)
        T-&gt;&gt;B: publish("transfer.completed")
        B-&gt;&gt;N: уведомление клиенту
        B-&gt;&gt;R: запись в историю / аудит
    end
```

---

## Задание

Реализовать консольное приложение «Банковская система», разбитое на независимые модули.

### Базовые модули (обязательно все 9)

| № | Модуль | Ответственность |
|---|--------|-----------------|
| 1 | `core` | Ядро: контракты, реестр модулей, шина событий, контекст |
| 2 | `auth` | Регистрация и вход клиента, роли, сессии |
| 3 | `accounts` | Открытие и закрытие счетов, баланс, типы счетов |
| 4 | `deposits` | Пополнение счёта |
| 5 | `withdrawals` | Снятие с проверкой лимитов и баланса |
| 6 | `transfers` | Переводы между счетами (внутренние и «внешние») |
| 7 | `reports` | Выписка, история операций, экспорт (CSV/JSON) |
| 8 | `notifications` | Лог, «email»-заглушка, «SMS»-заглушка |
| 9 | `persistence` | Хранилище: память / JSON-файл / SQLite (сменное) |

### Дополнительные модули (минимум 4 на выбор)

| № | Модуль | Ответственность |
|---|--------|-----------------|
| 10 | `fees` | Комиссии за операции (настраиваемые правила) |
| 11 | `limits` | Дневные и месячные лимиты на операции |
| 12 | `fraud_control` | Блокировка подозрительных операций (по событиям) |
| 13 | `bonus_points` | Кэшбэк и бонусы за операции |
| 14 | `currency` | Конвертация валют, курсы |
| 15 | `savings` | Накопительные счета с процентами |
| 16 | `credits` | Кредиты, графики платежей |
| 17 | `scheduler` | Отложенные и периодические платежи |
| 18 | `audit_log` | Аудит всех действий |
| 19 | `admin` | Админ-панель: блокировка клиента, отчёты |
| 20 | `analytics` | Статистика: расходы по категориям, топ операций |

> Минимум: 9 базовых + 4 дополнительных модуля.

---

## Требования к архитектуре

### 1. Контракт модуля
```python
# core/module.py
from abc import ABC, abstractmethod
from typing import Protocol


class ModuleContext(Protocol):
    """То, что ядро отдаёт каждому модулю."""
    events: "EventBus"
    registry: "Registry"

# сервисы других модулей через протоколы
    config: dict
    logger: "Logger"


class BankModule(ABC):
    name: str

    @abstractmethod
    def initialize(self, ctx: ModuleContext) -&gt; None: ...

    @abstractmethod
    def register_commands(self, cli: "CommandRegistry") -&gt; None: ...

    def shutdown(self) -&gt; None:
        """Опционально."""
```

### 2. Ядро не импортирует модули

Модули подключаются через entry points в `pyproject.toml`:
```toml
[project.entry-points."bank.modules"]
accounts      = "bank_modules.accounts:AccountsModule"
deposits      = "bank_modules.deposits:DepositsModule"
withdrawals   = "bank_modules.withdrawals:WithdrawalsModule"
transfers     = "bank_modules.transfers:TransfersModule"
# ...
```

Ядро загружает их через `importlib.metadata.entry_points(group="bank.modules")`, а затем оставляет только те, что перечислены в `config.toml`.

### 3. Межмодульное взаимодействие только через события и протоколы
```python
ctx.events.publish("money.deposited", {
    "account_id": acc_id,
    "amount": amount,

# в копейках, int
    "currency": "RUB",
})
```

Прямых импортов вида `from bank_modules.notifications import ...` внутри `deposits` быть не должно. Бизнес-модули импортируют только `core.protocols` и `core.events`.

### 4. Изоляция состояния

Каждый модуль хранит свои данные сам. К чужим данным он обращается только через `ctx.registry` и только по протоколу.

### 5. Деньги

Суммы хранятся в минимальных единицах валюты (копейках) как `int`. Тип `float` для денег использовать запрещено.

### 6. Отклонение операций

Проверяющие модули (`limits`, `fraud_control`, `withdrawals`) подписываются на события `*.requested`. Чтобы запретить операцию, они выбрасывают `OperationRejected` из `core.events`. Модуль, инициировавший операцию, ловит исключение и публикует `*.rejected`.

---

## Примеры контрактов ядра
```python
# core/events.py
from collections import defaultdict
from typing import Any, Callable


class OperationRejected(Exception):
    """Подписчик запрещает операцию."""


class EventBus:
    def __init__(self) -&gt; None:
        self._subs: dict[str, list[Callable[[dict], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[dict], None]) -&gt; None:
        self._subs[topic].append(handler)

    def publish(self, topic: str, payload: dict[str, Any]) -&gt; None:
        for handler in self._subs.get(topic, []):
            handler(payload)
```
```python
# core/protocols.py
from typing import Protocol, runtime_checkable


@runtime_checkable
class AccountsAPI(Protocol):
    def get_balance(self, account_id: str) -&gt; int: ...
    def exists(self, account_id: str) -&gt; bool: ...


@runtime_checkable
class Repository(Protocol):
    def save(self, entity: dict) -&gt; None: ...
    def get(self, entity_id: str) -&gt; dict | None: ...
    def all(self) -&gt; list[dict]: ...
```

---

## Минимальный список событий

Таблицу можно расширять, но эти события должны быть в каждой работе.

| Событие | Публикует | Слушают | Payload |
|---------|-----------|---------|---------|
| `user.registered` | `auth` | `notifications`, `audit_log` | `user_id`, `login`, `role` |
| `user.logged_in` | `auth` | `audit_log`, `fraud_control` | `user_id`, `ts` |
| `account.opened` | `accounts` | `notifications`, `reports` | `account_id`, `owner_id`, `type`, `currency` |
| `account.closed` | `accounts` | `notifications`, `reports` | `account_id` |
| `deposit.requested` | `deposits` | `limits`, `fraud_control` | `account_id`, `amount`, `currency` |
| `money.deposited` | `deposits` | `notifications`, `reports`, `bonus_points` | `operation_id`, `account_id`, `amount`, `currency`, `ts` |
| `withdrawal.requested` | `withdrawals` | `limits`, `fraud_control` | `account_id`, `amount` |
| `money.withdrawn` | `withdrawals` | `notifications`, `reports`, `analytics` | `operation_id`, `account_id`, `amount`, `ts` |
| `transfer.requested` | `transfers` | `limits`, `fraud_control`, `fees` | `from`, `to`, `amount`, `currency` |
| `transfer.completed` | `transfers` | `notifications`, `reports`, `bonus_points` | `operation_id`, `from`, `to`, `amount`, `fee`, `ts` |
| `transfer.rejected` | `transfers` | `notifications`, `audit_log` | `from`, `to`, `amount`, `reason` |
| `fee.charged` | `fees` | `reports` | `operation_id`, `account_id`, `fee` |
| `fraud.detected` | `fraud_control` | `admin`, `notifications` | `user_id`, `operation`, `reason` |
| `operation.reversed` | `reports` / `admin` | `accounts`, `notifications` | `operation_id`, `reason` |

---

## Обязательный функционал

### Базовый сценарий

1. Регистрация и вход клиента.
2. Открытие счёта (текущий или сберегательный).
3. Пополнение счёта.
4. Снятие с проверкой баланса и лимитов.
5. Перевод между счетами.
6. Выписка по счёту (фильтр по датам и типу операций).
7. Логирование и уведомление о каждой операции.

### Расширенный функционал (минимум 8 пунктов)

- [ ] Роли: `клиент` / `админ`.
- [ ] Комиссии за переводы (`fees`).
- [ ] Дневные и месячные лимиты (`limits`).
- [ ] Блокировка подозрительных операций (`fraud_control`).
- [ ] Кэшбэк и бонусы (`bonus_points`).
- [ ] Мультивалютность и конвертация (`currency`).
- [ ] Накопительные счета с процентами (`savings`).
- [ ] Кредиты с графиком платежей (`credits`).
- [ ] Отложенные и периодические платежи (`scheduler`).
- [ ] Аудит действий (`audit_log`).
- [ ] Админ-панель (`admin`).
- [ ] Аналитика расходов по категориям (`analytics`).
- [ ] Экспорт выписки в CSV/JSON.
- [ ] Откат операции (reversal) через событие.

> Отметьте выполненные пункты в своём `README.md`, поставив `[x]`.

---

## Обязательные демонстрации независимости

Каждую демонстрацию нужно подтвердить логом или скриншотом, а также `git diff`, где видно, что код других модулей не менялся.

| № | Эксперимент | Что меняется | Что не должно меняться |
|---|-------------|--------------|-----------------------------|
| 1 | Отключение модуля | `config.toml` (убрать, например, `fees`) | Код любых модулей |
| 2 | Замена `persistence` | `persistence.backend = "sqlite"` | `accounts`, `transfers` и прочие |
| 3 | Добавление нового модуля | Новый пакет `bonus_points` + entry point | Существующие модули |
| 4 | Замена `notifications` | `channels = ["email"]` вместо `["log"]` | Бизнес-модули |

---

## Пример конфигурации
```toml
# config.toml
[modules]
enabled = [
    "auth", "accounts", "deposits", "withdrawals", "transfers",
    "reports", "notifications", "persistence",
    "fees", "limits", "fraud_control", "audit_log",
]

[persistence]
backend = "sqlite"

# memory | json | sqlite
path = "data/bank.db"

[notifications]
channels = ["log", "email"]

[fees]
transfer_percent = 1.0
min_fee = 1000

# копейки

[limits]
daily_withdrawal = 10_000_000
monthly_transfer = 50_000_000

[fraud_control]
max_operations_per_minute = 5
large_amount = 20_000_000
```

---

## Структура проекта
```
bank-system/
├── pyproject.toml
├── config.toml
├── README.md
├── .importlinter
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── module.py

# BankModule, ModuleContext
│   │   ├── events.py

# EventBus, OperationRejected
│   │   ├── protocols.py

# общие протоколы
│   │   ├── registry.py

# Registry
│   │   ├── loader.py

# загрузка через entry_points
│   │   └── cli.py

# CommandRegistry
│   ├── bank_modules/
│   │   ├── auth/
│   │   ├── accounts/
│   │   ├── deposits/
│   │   ├── withdrawals/
│   │   ├── transfers/
│   │   ├── reports/
│   │   ├── notifications/
│   │   ├── persistence/
│   │   └── ...

# дополнительные
│   └── host/
│       └── main.py

# точка входа
├── tests/
│   ├── test_accounts.py
│   ├── test_transfers.py
│   ├── test_isolation.py

# тесты независимости
│   └── ...
└── docs/
    ├── report.md

# отчёт
    └── screenshots/
```

---

## Автоматическая проверка независимости

Запрет на перекрёстные импорты проверяется утилитой [import-linter](https://github.com/seddonym/import-linter):
```ini
# .importlinter
[importlinter]
root_packages =
    core
    bank_modules
    host

[importlinter:contract:core-independent]
name = Ядро не импортирует модули
type = forbidden
source_modules = core
forbidden_modules = bank_modules

[importlinter:contract:modules-independent]
name = Модули не импортируют друг друга
type = independence
modules =
    bank_modules.auth
    bank_modules.accounts
    bank_modules.deposits
    bank_modules.withdrawals
    bank_modules.transfers
    bank_modules.reports
    bank_modules.notifications
    bank_modules.persistence
```

Минимальный CI (`.github/workflows/ci.yml`) должен запускать:
```bash
pip install -e ".[dev]"
lint-imports
pytest --cov=src --cov-fail-under=70
```

---

## Запуск
```bash
git clone &lt;ссылка на ваш репозиторий&gt;
cd bank-system
python -m venv .venv
source .venv/bin/activate

# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m host.main --config config.toml
```

---

## Порядок сдачи

1. Создайте репозиторий из этого шаблона (Use this template) или сделайте fork.
2. Ведите работу в ветке `lab/<фамилия>`, коммиты делайте осмысленными.
3. Откройте Pull Request в свою ветку `main`.
4. CI должен быть зелёным: тесты проходят, `lint-imports` без ошибок.
5. Положите отчёт в `docs/report.md`.
6. Отправьте преподавателю ссылку на PR.

---

## Форма отчёта (`docs/report.md`)

1. Схема модулей (Mermaid / PlantUML / draw.io) с зависимостями.
2. Описание контрактов: `BankModule`, `ModuleContext`, ключевые протоколы.
3. Таблица событий: имя, кто публикует, кто слушает, payload.
4. Демонстрации независимости (минимум 3 из 4) с логами, скриншотами и `git diff`.
5. Инструкция по запуску.
6. Пример конфигурации (`config.toml`).
7. Логи или скриншоты базового сценария.
8. Выводы: что было сложно и где пришлось нарушить изоляцию (если пришлось), с объяснением.

---

## Критерии оценки

| Критерий | Баллы |
|----------|-------|
| Ядро: контракты, загрузчик, шина, реестр | 15 |
| 9 базовых модулей, базовый сценарий работает | 20 |
| Минимум 4 дополнительных модуля | 15 |
| Минимум 8 пунктов расширенного функционала | 10 |
| Нет перекрёстных импортов (`lint-imports` проходит) | 10 |
| Демонстрации независимости | 15 |
| Тесты (покрытие ≥ 70 %, есть `test_isolation.py`) | 10 |
| Отчёт и качество кода (type hints, docstrings, README) | 5 |
| Итого | 100 |

Штрафы:

- прямой импорт одного бизнес-модуля в другой: −10 за каждый случай;
- `float` для денежных сумм: −5;
- CI не проходит: работа не принимается.

---

## Полезные ссылки

- [importlib.metadata — entry points](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [import-linter](https://import-linter.readthedocs.io/)
- [Mermaid в GitHub](https://docs.github.com/ru/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
