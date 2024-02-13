import logging
import time
from datetime import datetime
from telegram import Update
from exchange import CurrencyExchange
from database import Base, SessionLocal, engine
from models import User
from functools import wraps
import telegram
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from dotenv import load_dotenv
import os


load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


Base.metadata.create_all(bind=engine)
db = SessionLocal()


api_key = os.getenv("api_key")
currency_exchange = CurrencyExchange(api_key)


def for_registered_users(f):
    @wraps(f)
    async def wrapper_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = db.query(User).filter_by(chat_id=update.effective_chat.id).first()
        if not user:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="This endpoint is for registered users."
            )
        else:
            await f(update, context)

    return wrapper_function


def for_new_users(f):
    @wraps(f)
    async def wrapper_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = db.query(User).filter_by(chat_id=update.effective_chat.id).first()
        if user:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="This endpoint is for new and unregistered users."
            )
        else:
            await f(update, context)

    return wrapper_function


@for_new_users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to the currency exchange bot.\n\n"
             "What is your base currency? Use the example below as a guide:\n\n"
             "/baseCurrency\n"
             "your base currency, e.g USD, GBP, CAD, etc.\n\n",
        parse_mode=telegram.constants.ParseMode.HTML
    )


@for_new_users
async def record_base_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Record Base Currency """

    argument = "".join(context.args)
    base_currency = str(argument).upper()

    if currency_exchange.is_valid_currency(base_currency):
        context.user_data["base_currency"] = base_currency

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Kindly list your favorite target currencies. That is, a list of currencies you want to convert"
                 " your base currency to. You can select as many as you want\n"
                 "<b>Each currency should be separated by a comma(,)</b>\n\n"
                 "Use the example below as a guide:\n\n"
                 "/targetCurrencies\n"
                 "USD,CAD,GBP",
            parse_mode=telegram.constants.ParseMode.HTML
            )

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"This bot does not support {base_currency} currency"
        )


@for_new_users
async def record_target_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arguments = "".join(context.args)
    currency_pairs = arguments.split(",")
    if currency_exchange.is_valid_currencies(currency_pairs):
        context.user_data["target_currencies"] = arguments

        keyboard = [[InlineKeyboardButton('Yes', callback_data='yes')],
                    [InlineKeyboardButton('No', callback_data='no')]]

        await update.message.reply_text(
            text="<b>Would you like to receive daily updates on selected currencies?</b>",
            parse_mode=telegram.constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error occurred! Ensure that each currency is supported by the bot."
        )


@for_new_users
async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ User completes registration """
    query = update.callback_query.data
    try:
        target_currencies = context.user_data.get("target_currencies")
        base_currency = context.user_data.get("base_currency")
    except KeyError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="<b>There's an error with your registration. Kindly restart by submitting your base currency</b>\n"
                 "Use the example below as a guide:\n\n"
                 "/baseCurrency\n"
                 "your base currency, e.g USD, GBP\n\n",
            parse_mode=telegram.constants.ParseMode.HTML
        )
    else:
        if query == "yes":
            receive_updates = True
        else:
            receive_updates = False

        new_user = User(
            chat_id=update.effective_chat.id,
            base_currency=base_currency,
            currency_pairs=target_currencies,
            receive_updates=receive_updates
        )
        db.add(new_user)
        db.commit()

        options = [["Activate Updates 🚀", 'Deactivate updates'], ['Bot Manual 📗']]

        key_markup = ReplyKeyboardMarkup(options, resize_keyboard=True)
        await context.bot.send_message(text="<b>You have successfully completed your registration</b>",
                                       reply_markup=key_markup,
                                       chat_id=update.effective_chat.id,
                                       parse_mode=telegram.constants.ParseMode.HTML)


@for_registered_users
async def direct_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Direct messages """
    message = update.message.text
    user = db.query(User).filter_by(chat_id=update.effective_chat.id).first()

    if message == "Bot Manual 📗":
        await context.bot.send_message(
            text="<i>Click <b>Activate Updates</b> to activate daily updates</i>\n\n"
                 "<i>Click <b>Deactivate Updates</b> to deactivate updates</i>\n\n"
                 "<i>Click <b>Bot Manual</b> to learn how to use the bot</i>\n\n"
                 ""
                 "<i>To find the exchange rate between a base currency and multiple target currencies, use the command "
                 "below:\n\n</i>"
                 "/multipleExchange\n"
                 "USD/CAD/EUR\n\n"
                 "Put your base currency first and other currencies should follow. Separate them with a forward "
                 "slash(/)\n\n"
                 ""
                 "<i>To find the exchange rate between a base currency a single target currency, use the command "
                 "below:</i>\n\n"
                 "/singleExchange\n"
                 "USD/GBP\n\n"
                 "Put your base currency first and the target currency should follow. Separate them with a forward "
                 "slash(/).\n\n"
                 ""
                 "<i>To find the exchange rate between a base currency a single target currency with a base amount, "
                 "use the command below:</i>\n\n"
                 "/exchangeRate\n"
                 "USD/CAD @ 50\n\n"
                 "Put your base and target currency together and signify the base amount with the @ symbol",
            chat_id=update.effective_chat.id,
            parse_mode=telegram.constants.ParseMode.HTML)

    elif message == "Activate Updates 🚀":
        user.receive_updates = True
        db.commit()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="<i>You have successfully activated daily exchange rate updates</i>",
            parse_mode=telegram.constants.ParseMode.HTML
        )

    elif message == 'Deactivate updates':
        user.receive_updates = False
        db.commit()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="<i>You have successfully deactivated daily exchange rate updates</i>",
            parse_mode=telegram.constants.ParseMode.HTML
        )

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="<i>This bot is not able to respond to your messages for now</i>",
            parse_mode=telegram.constants.ParseMode.HTML
        )


@for_registered_users
async def single_exchange_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Exchange Currencies """
    currency_pairs = "".join(context.args)

    try:
        base_currency = currency_pairs.split("/")[0].upper()
        target_currency = currency_pairs.split("/")[1].upper()
    except IndexError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error occurred! You must enter two currency codes separated by a forward slash(/)"
        )
    else:
        if currency_exchange.is_valid_currency(base_currency) and currency_exchange.is_valid_currency(target_currency):
            params = {
                "base": base_currency,
                "target": target_currency
            }

            response = currency_exchange.single_exchange(params=params)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>Base Currency:</b> {base_currency}\n"
                     f"<b>Target Currency:</b> {target_currency}\n"
                     f"<b>Exchange Rate</b>: {response['exchange_rate']}\n\n"
                     f"<i>This means that 1 {base_currency} is equal to {response['exchange_rate']} {target_currency}</i>",
                parse_mode=telegram.constants.ParseMode.HTML
            )

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error occurred! Ensure that both currencies are supported by the bot."
            )


@for_registered_users
async def multiple_exchange_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Exchange Currencies """
    argument = "".join(context.args)
    currency_pairs = argument.split("/")

    try:
        base_currency = currency_pairs[0]
        target_currencies_list = currency_pairs[1:]

    except IndexError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error occurred! Ensure that there are more than two currencies separated by a forward slash(/)."
        )
    else:
        if currency_exchange.is_valid_currencies(target_currencies_list):
            print(target_currencies_list)
            target_currencies = ",".join(target_currencies_list)

            params = {
                "base": base_currency,
                "target": target_currencies
            }

            response = currency_exchange.multiple_exchange(params=params)
            print(response)
            result = []
            for currency in target_currencies_list:
                rate = response["exchange_rates"][currency]
                result.append(f"<b>{currency}</b> = {rate}\n")

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="".join(result),
                parse_mode=telegram.constants.ParseMode.HTML
            )

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error occurred! Ensure this bot supports the currencies you entered."
            )


@for_registered_users
async def arbitrary_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Exchange Currencies """
    arguments = "".join(context.args)
    split_arguments = arguments.split("@")

    try:
        base_currency = split_arguments[0].split("/")[0]
        target_currency = split_arguments[0].split("/")[1]
        base_amount = float(split_arguments[1])

    except IndexError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please enter values in the correct format"
        )

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please enter a valid number"
        )
    else:
        if currency_exchange.is_valid_currency(base_currency) and currency_exchange.is_valid_currency(target_currency):
            params = {
                "base": base_currency,
                "target": target_currency,
                "base_amount": base_amount
            }

            response = currency_exchange.single_exchange(params=params)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>Base Currency:</b> {base_currency}\n"
                     f"<b>Target Currency:</b> {target_currency}\n"
                     f"<b>Exchange Rate:</b> {response['exchange_rate']}\n\n"
                     f"<i>This means that {response['base_amount']} {base_currency} is equal to "
                     f"{response['converted_amount']} {target_currency}</i>",
                parse_mode=telegram.constants.ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error occurred! Ensure this bot supports the currencies you entered."
            )


async def daily_updates(context: ContextTypes.DEFAULT_TYPE):
    all_users = db.User.all()
    will_receive_updates = [user for user in all_users if user.receive_updates is True]
    context.bot_data['cached_rates'] = {}

    async def send_update(user):
        base_currency = user.base_currency.upper()
        params = {
            "base": base_currency
        }
        chat_id = user.chat_id

        currency_pairs = user.currency_pairs.split(",")

        response = ""
        try:
            cached_response = context.bot_data['cached_rates'][base_currency]
        except KeyError:
            response = currency_exchange.multiple_exchange(params)
        else:
            response = cached_response

        update_message = f"<b>Latest update on exchange rates relative to {base_currency}</b>\n" \
                         f"This means that 1 {base_currency} is equal to the following in different currencies:\n\n" \
                         f""
        for currency in currency_pairs:
            exchange_rate = response['exchange_rates'][currency.upper()]
            update_message += f"<b>{currency}</b>: {exchange_rate}\n"

        context.bot_data['recent_exchange_rates'][base_currency] = response
        await context.bot.send_message(
            chat_id=chat_id,
            text=update_message,
            parse_mode=telegram.constants.ParseMode.HTML
        )

    for user in will_receive_updates:
        await send_update(user)
        time.sleep(2)

    context.bot_data.clear()


if __name__ == "__main__":

    TOKEN = os.getenv("token")
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    # unknown_handler = MessageHandler(filters.COMMAND, unknown_commands)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), direct_messages)
    base_currency_handler = CommandHandler('baseCurrency', record_base_currency)
    target_currency_handler = CommandHandler('targetCurrencies', record_target_currencies)

    exchange_handlers = [CommandHandler('singleExchange', single_exchange_rate),
                         CommandHandler("multipleExchange", multiple_exchange_rate),
                         CommandHandler("exchangeRate", arbitrary_exchange)]

    callback_handlers = [CallbackQueryHandler(complete_registration, 'yes'),
                         CallbackQueryHandler(complete_registration, 'no')]

    # Add handlers

    application.add_handler(start_handler)
    application.add_handler(message_handler)
    application.add_handler(base_currency_handler)
    application.add_handler(target_currency_handler)
    application.add_handlers(callback_handlers)
    application.add_handlers(exchange_handlers)

    time_format = '%H:%M'

    # SET REMINDER
    reminder_time_string = '07:00'
    daily_job = application.job_queue
    datetime_obj = datetime.strptime(reminder_time_string, time_format)
    daily_job.run_daily(daily_updates, time=datetime_obj.time(), days=tuple(range(7)))

    # Start app
    application.run_polling()