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

## Структура проекта (пример)
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
## Полезные ссылки

- [Модульное программирование: принципы, выгоды и реализация в коде](https://sky.pro/wiki/javascript/modulnoe-programmirovanie-osnovy-preimushestva-primery/)
- [Модульное программирование в Python: структурирование кода правильно]([https://sky.pro/wiki/javascript/modulnoe-programmirovanie-osnovy-preimushestva-primery/](https://sky.pro/wiki/media/kak-sozdat-i-ispolzovat-sobstvennye-moduli-v-python/?ysclid=mwaje3875382771513))
- [Python модули и пакеты](https://habr.com/ru/articles/718828/)
- [importlib.metadata — entry points](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
- [typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [import-linter](https://import-linter.readthedocs.io/)
- [Mermaid в GitHub](https://docs.github.com/ru/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
