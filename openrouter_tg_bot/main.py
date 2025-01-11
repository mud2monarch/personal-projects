import logging, os, asyncio, aiohttp, json
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from dotenv import load_dotenv
load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_KEY')
GROK2 = "x-ai/grok-2-1212"
CLAUDE3_5 = "anthropic/claude-3.5-sonnet:beta"
LLAMA3_3 = "meta-llama/llama-3.3-70b-instruct"

COMMON_MODELS = {
    "GROK2": GROK2,
    "CLAUDE3_5": CLAUDE3_5,
    "LLAMA3_3": LLAMA3_3
}

model = GROK2

from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler

"""
Methods:
    CommandHandler /set_model - change the model to the user input
    CommandHandler /display_current_model - print the model currently in use
    MessageHandler openrouter_query - send the message to openrouter and report back the response
"""

# async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE)

async def query_openrouter(
    query: str,
    _model: str = model
) -> str:

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": f"x.com/mud2monarch",  # Optional, for including your app on openrouter.ai rankings.
                "X-Title": f"gyges",  # Optional. Shows in rankings on openrouter.ai.
            },
            data=json.dumps({
                "model": _model,  # Optional
                "messages": [
                    {
                        "role": "user",
                        "content": query},
                ],
            })
        ) as response:
            # Check if the request was successful
            if response.status == 200:
                # Parse the JSON response
                json_response = await response.json()
                # Extract the content of the AI's message
                ai_message = json_response['choices'][0]['message']['content']
                return ai_message
            else:
                # If the request failed, return an error message or handle it as needed
                return f"Error: {response.status} - {await response.text()}"

async def openrouter_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    text = await query_openrouter(query, model)
    await update.message.reply_text(text)

async def display_current_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text(f"current model is {model}.")

async def display_all_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model_list = "\n".join(f"{key}: {value}" for key, value in COMMON_MODELS.items())
    await update.message.reply_text(f"common models include \n{model_list}")

async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = update.message.text # See https://docs.python-telegram-bot.org/en/stable/telegram.ext.commandhandler.html
    await update.message.reply_text(f"changed the model to {model}.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    openrouterSend = MessageHandler(filters.TEXT & (~filters.COMMAND), openrouter_query)
    application.add_handler(openrouterSend)
    displayModel = CommandHandler('display_current_model', display_current_model)
    application.add_handler(displayModel)
    displayAllModels = CommandHandler('display_all_models', display_all_models)
    application.add_handler(displayAllModels)

    application.run_polling()