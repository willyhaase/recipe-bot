import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

from spoonacular_client import SpoonacularClient
from claude_client import ClaudeClient

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_MODE, WAITING_INPUT, SHOWING_RECIPES = range(3)

spoonacular = SpoonacularClient(os.getenv("SPOONACULAR_API_KEY"))
claude = ClaudeClient(os.getenv("ANTHROPIC_API_KEY"))


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🥕 За інгредієнтами", callback_data="mode_ingredients"),
            InlineKeyboardButton("🍽 За назвою", callback_data="mode_name"),
        ],
        [
            InlineKeyboardButton("📂 За категорією", callback_data="mode_category"),
            InlineKeyboardButton("🤖 Запитати AI", callback_data="mode_ai"),
        ],
    ])


def categories_keyboard():
    categories = [
        ("🍲 Супи", "main course"),
        ("🥗 Салати", "salad"),
        ("🍰 Десерти", "dessert"),
        ("🥞 Сніданки", "breakfast"),
        ("🥙 Закуски", "appetizer"),
        ("🍹 Напої", "beverage"),
    ]
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"cat_{slug}")]
        for name, slug in categories
    ]
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def recipe_keyboard(recipes: list):
    buttons = []
    for r in recipes:
        title = r["title"][:40] + ("…" if len(r["title"]) > 40 else "")
        buttons.append([InlineKeyboardButton(f"📖 {title}", callback_data=f"recipe_{r['id']}")])
    buttons.append([InlineKeyboardButton("🔙 До меню", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👨‍🍳 *Привіт! Я бот для пошуку рецептів.*\n\n"
        "Я вмію шукати рецепти за інгредієнтами, назвою або категорією.\n"
        "Також можна запитати AI-шефа — він придумає рецепт спеціально для тебе!\n\n"
        "Обери, як будемо шукати:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )
    return CHOOSING_MODE


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 *Як користуватися ботом:*\n\n"
        "• *За інгредієнтами* — напиши що є в холодильнику, наприклад: `курка, картопля, цибуля`\n"
        "• *За назвою* — напиши назву страви, наприклад: `борщ`\n"
        "• *За категорією* — обери зі списку (супи, салати, десерти...)\n"
        "• *Запитати AI* — постав питання своїми словами, наприклад: `що приготувати із залишків пасти?`\n\n"
        "/start — повернутися до головного меню",
        parse_mode=ParseMode.MARKDOWN,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        await query.edit_message_text(
            "Обери спосіб пошуку:",
            reply_markup=main_menu_keyboard(),
        )
        return CHOOSING_MODE

    if data == "mode_ingredients":
        context.user_data["mode"] = "ingredients"
        await query.edit_message_text(
            "🥕 *Пошук за інгредієнтами*\n\n"
            "Напиши через кому що є у тебе вдома.\n"
            "_Приклад: курка, картопля, цибуля, часник_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return WAITING_INPUT

    if data == "mode_name":
        context.user_data["mode"] = "name"
        await query.edit_message_text(
            "🍽 *Пошук за назвою*\n\n"
            "Напиши назву страви, яку хочеш знайти.\n"
            "_Приклад: паста карбонара_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return WAITING_INPUT

    if data == "mode_ai":
        context.user_data["mode"] = "ai"
        await query.edit_message_text(
            "🤖 *AI-шеф*\n\n"
            "Постав будь-яке питання або опиши ситуацію.\n"
            "_Наприклад: що приготувати на вечерю з курячого філе за 30 хвилин?_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return WAITING_INPUT

    if data == "mode_category":
        await query.edit_message_text(
            "📂 *Обери категорію:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=categories_keyboard(),
        )
        return CHOOSING_MODE

    if data.startswith("cat_"):
        category = data[4:]
        await query.edit_message_text("⏳ Шукаю рецепти...")
        recipes = await spoonacular.search_by_category(category, number=8)
        if not recipes:
            await query.edit_message_text(
                "😕 Нічого не знайшлося. Спробуй іншу категорію.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад", callback_data="mode_category")
                ]])
            )
            return CHOOSING_MODE
        context.user_data["recipes"] = recipes
        await query.edit_message_text(
            f"✅ Знайшов *{len(recipes)}* рецептів. Обирай:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=recipe_keyboard(recipes),
        )
        return SHOWING_RECIPES

    if data.startswith("recipe_"):
        recipe_id = int(data[7:])
        await query.edit_message_text("⏳ Завантажую рецепт...")
        recipe = await spoonacular.get_recipe_details(recipe_id)
        if not recipe:
            await query.edit_message_text("😕 Не вдалося завантажити рецепт.")
            return SHOWING_RECIPES

        await query.edit_message_text("🌐 Перекладаю на українську...")
        text = format_recipe(recipe)
        text = await claude.translate_recipe(text)
        back_btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ До списку", callback_data="show_list"),
            InlineKeyboardButton("🏠 До меню", callback_data="back_main"),
        ]])
        if len(text) > 4000:
            text = text[:3990] + "\n\n_...рецепт скорочено_"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_btn)
        return SHOWING_RECIPES

    if data == "show_list":
        recipes = context.user_data.get("recipes", [])
        if not recipes:
            await query.edit_message_text("Список порожній.", reply_markup=main_menu_keyboard())
            return CHOOSING_MODE
        await query.edit_message_text(
            "Обери рецепт:",
            reply_markup=recipe_keyboard(recipes),
        )
        return SHOWING_RECIPES

    return CHOOSING_MODE


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    text = update.message.text.strip()

    if not mode:
        await update.message.reply_text(
            "Будь ласка, обери режим пошуку:",
            reply_markup=main_menu_keyboard(),
        )
        return CHOOSING_MODE

    thinking_msg = await update.message.reply_text("⏳ Шукаю рецепти...")

    if mode == "ingredients":
        recipes = await spoonacular.search_by_ingredients(text, number=8)
    elif mode == "name":
        recipes = await spoonacular.search_by_name(text, number=8)
    elif mode == "ai":
        response = await claude.ask_chef(text)
        await thinking_msg.edit_text(
            f"🤖 *AI-шеф радить:*\n\n{response}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 До меню", callback_data="back_main"),
                InlineKeyboardButton("🤖 Ще питання", callback_data="mode_ai"),
            ]])
        )
        return WAITING_INPUT
    else:
        recipes = []

    if not recipes:
        await thinking_msg.edit_text(
            "😕 Нічого не знайшлося. Спробуй інший запит.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 До меню", callback_data="back_main")
            ]])
        )
        return CHOOSING_MODE

    context.user_data["recipes"] = recipes
    await thinking_msg.edit_text(
        f"✅ Знайшов *{len(recipes)}* рецептів за запитом «{text}».\nОбирай:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=recipe_keyboard(recipes),
    )
    return SHOWING_RECIPES


def format_recipe(recipe: dict) -> str:
    import re
    title = recipe.get("title", "Без назви")
    ready_in = recipe.get("readyInMinutes", "?")
    servings = recipe.get("servings", "?")
    source = recipe.get("sourceUrl", "")

    ingredients = recipe.get("extendedIngredients", [])
    ing_lines = [f"• {i.get('original', '')}" for i in ingredients[:20]]
    ing_text = "\n".join(ing_lines) if ing_lines else "_немає даних_"

    instructions_raw = recipe.get("instructions", "") or ""
    instructions_clean = re.sub(r"<[^>]+>", "", instructions_raw).strip()
    if len(instructions_clean) > 1500:
        instructions_clean = instructions_clean[:1500] + "…"
    if not instructions_clean:
        instructions_clean = "_інструкції недоступні_"

    text = (
        f"🍽 *{title}*\n\n"
        f"⏱ Час: {ready_in} хв  |  👥 Порцій: {servings}\n\n"
        f"*Інгредієнти:*\n{ing_text}\n\n"
        f"*Приготування:*\n{instructions_clean}\n"
    )
    if source:
        text += f"\n[📎 Повний рецепт]({source})"
    return text


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задано в .env")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_MODE: [CallbackQueryHandler(button_handler)],
            WAITING_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
                CallbackQueryHandler(button_handler),
            ],
            SHOWING_RECIPES: [CallbackQueryHandler(button_handler)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_command))

    logger.info("Бот запущено!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
