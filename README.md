# 🍳 Recipe Bot — Telegram бот для пошуку рецептів

Бот шукає рецепти за інгредієнтами, назвою та категоріями через Spoonacular API,
а також відповідає на кулінарні питання за допомогою Claude AI українською мовою.

## Можливості

- 🥕 **Пошук за інгредієнтами** — напиши що є в холодильнику
- 🍽 **Пошук за назвою** — знайди будь-яку страву
- 📂 **За категорією** — супи, салати, десерти, сніданки, закуски, напої
- 🤖 **AI-шеф** — постав питання Claude, отримай персональну пораду

## Встановлення

### 1. Отримай API ключі

| Сервіс | Де отримати | Безкоштовно |
|--------|-------------|-------------|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) → `/newbot` | ✅ |
| Spoonacular API Key | [spoonacular.com/food-api](https://spoonacular.com/food-api) | ✅ 150 запитів/день |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) | платно |

### 2. Встанови залежності

```bash
pip install -r requirements.txt
```

### 3. Налаштуй змінні середовища

```bash
cp .env.example .env
# Відкрий .env і встав свої ключі
```

### 4. Запусти бота

```bash
python bot.py
```

## Структура проєкту

```
recipe_bot/
├── bot.py                 # Основна логіка бота
├── spoonacular_client.py  # Клієнт Spoonacular API
├── claude_client.py       # Клієнт Claude AI
├── requirements.txt
├── .env.example
└── README.md
```

## Команди бота

- `/start` — головне меню
- `/help` — довідка з використання

## Приклади запитів

- За інгредієнтами: `курка, картопля, цибуля, часник`
- За назвою: `паста карбонара`, `борщ`, `тірамісу`
- AI-питання: `що приготувати з курячого філе за 30 хвилин?`

## Деплой (за потреби)

```bash
# Простий спосіб — запуск у фоні
nohup python bot.py &

# Або через screen
screen -S recipe_bot
python bot.py
# Ctrl+A, D — вийти, залишивши бота працювати
```
