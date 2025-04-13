# Shot‑Folder‑CLI

Утилита для создания стандартной иерархии папок для шотов в Google Drive  
с использованием **Service Account** и Google Drive API.

---

## 🚀 Возможности

- Создание **N шотов**: shot_0010, shot_0020, …  
- Создание **одного шота**: shot_0015 (или любое имя по формату)
- Проверка существующей структуры (`verify`)
- Бесконечный **интерактивный режим** — скрипт работает как бот, постоянно спрашивая, что делать.
- Надёжные повторные попытки (retry) при ошибках Google API (через `tenacity`)
- Настраиваемая структура папок в `structure.json`

---

## 📦 Установка

1. Установи Python 3.9+  
2. Склонируй/скачай проект и перейди в папку:

```bash
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
⚙ Настройка
Включи Google Drive API в Google Cloud Console

Создай Service Account, скачай ключ → положи рядом с проектом как service_account.json

Поделись своей Google Drive папкой с этим аккаунтом (email вида: xxx@project.iam.gserviceaccount.com) и выдай права Editor

Скопируй файл:

bash
نسخ
تحرير
cp config.json.example config.json
И впиши google_root_id — это ID папки из адресной строки Google Диска:

ruby
نسخ
تحرير
https://drive.google.com/drive/folders/**ID_ЗДЕСЬ**
🧑‍💻 Использование
▶ Интерактивный режим (рекомендуется)
bash
نسخ
تحرير
python main.py
Скрипт будет бесконечно спрашивать:

30 → создаст 30 шотов (shot_0010 … shot_0300)

shot_0075 → создаст один шот с нужным именем

verify → проверит, все ли папки созданы

Enter → завершить

💻 Командная строка (CLI)
bash
نسخ
تحرير
python main.py create 20
python main.py single shot_0065
python main.py verify
🧱 Структура создаваемых шотов
Структура берётся из structure.json и может быть изменена вручную.

Пример (по умолчанию):

mathematica
نسخ
تحرير
shot_0010/
├── Concept_Art/
│   ├── In
│   ├── Progress
│   └── Out
├── Lookdev/
│   ├── In
│   ├── Progress
│   └── Out
├── Animation/
│   ├── Face/
│   │   ├── Record/
│   │   └── Cleanup/
│   └── Body/
│       ├── Record/
│       └── Cleanup/
├── Cloth_Simulate/
├── Fx/
└── Compositing/
📁 Структура проекта
bash
نسخ
تحرير
project/
├── main.py                 # точка входа (интерактив + CLI)
├── structure.json          # структура создаваемых папок
├── config.json.example     # шаблон для Google Drive root ID
├── service_account.json    # 🔒 ключ сервисного аккаунта (НЕ коммитить!)
├── requirements.txt        # зависимости
└── README.md               # этот файл
🛠 Зависимости
txt
نسخ
تحرير
google-api-python-client
google-auth
google-auth-httplib2
rich
typer
tenacity
🧠 Примеры
Создание 5 шотов:

bash
نسخ
تحرير
python main.py
Введите число, имя или verify: 5
Создание одного конкретного:

bash
نسخ
تحرير
Введите число, имя или verify: shot_0055
Проверка:

bash
نسخ
تحرير
Введите число, имя или verify: verify
