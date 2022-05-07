import telebot
from telebot import types
from quiz import *
import html
from collections import defaultdict
from utils import *
import os

# TODO Save state
# TODO Show high scores
# Commands for bot
COMMANDS = ['quit', 'cat_ch', 'dif_ch']
BOT_COMMANDS = [
    types.BotCommand('quit', 'Закончить текущий квиз.'),
    types.BotCommand('cat_ch', 'Сменить категорию вопросов.'),
    types.BotCommand('dif_ch', 'Сменить сложность вопросов.')
]

# Stickers id
STICKER_5_ID = 'CAACAgQAAxkBAAIBe2J0TZsDUnAygMq-Y1CTop3Zof8OAALZCAAC2SJ5Unec3QvlsgvJJAQ'
STICKER_10_ID = 'CAACAgQAAxkBAAIBfWJ0TmHB3aCfFN602ff0ngp_W6rSAAKnDAACJsx4Urk28QaF_q_6JAQ'

# Available user states
USER_STATES = (
    'joined', 'created', 'started', 'ready to play', 'category chosen', 'difficulty chosen', 'questions asked'
)

# Quiz api parameters
NESTED_CATEGORIES = ('entertainment', 'science')
DIFFICULTY_LEVELS = ('easy', 'medium', 'hard')
ALL_CATEGORIES = get_categories()
# Getting names for every category
CATEGORIES, SUB_CATEGORIES = parse_categories(ALL_CATEGORIES, NESTED_CATEGORIES)
SUB_NAMES = [name for values in SUB_CATEGORIES.values() for name in values]

# Bot internal settings
token = os.environ['TELEGRAM_TOKEN']
base_url = 'https://api.telegram.org/bot' + token
HEROKU = os.environ.get('HEROKU', False
                        )

bot = telebot.TeleBot(token)
USERS = dict()

# Setting bot commands and menu button
bot.set_my_commands(BOT_COMMANDS)
menu_button = types.MenuButtonCommands('commands')
bot.set_chat_menu_button(menu_button=menu_button)

# @bot.message_handler(content_types=['sticker'])
# def helper(message):
#     print(message.text, message.sticker)


@bot.message_handler(commands=COMMANDS)
def command(message):
    user_id = message.from_user.id
    user = USERS.get(user_id)
    if not user:
        user = prepare_user(message)
    if message.text == '/quit':
        bot.send_message(message.chat.id, 'Возвращаемся...', reply_markup=types.ReplyKeyboardRemove(selective=False))
        user.state = USER_STATES[1]
        message.text = '/start'
        greeting(message, user)
    elif message.text == '/cat_ch':
        if user.state in USER_STATES[:3]:
            bot.send_message(message.chat.id, 'Сначала начните игру.',
                             reply_markup=types.ReplyKeyboardRemove(selective=False))
        else:
            bot.send_message(message.chat.id, 'Возвращаемся...',
                             reply_markup=types.ReplyKeyboardRemove(selective=False))
            user.state = USER_STATES[3]
            show_categories(message)
    elif message.text == '/dif_ch':
        if user.state in USER_STATES[:4]:
            bot.send_message(message.chat.id, 'Сначала начните игру и выберите категорию.',
                             reply_markup=types.ReplyKeyboardRemove(selective=False))
        else:
            bot.send_message(message.chat.id, 'Возвращаемся...',
                             reply_markup=types.ReplyKeyboardRemove(selective=False))
            user.state = USER_STATES[4]
            process_difficulty(message)


@bot.message_handler(func=lambda message: True)
def main(message):
    user_id = message.from_user.id
    user = USERS.get(user_id)
    if not user:
        user = prepare_user(message)
        greeting(message, user)
    elif user.state == USER_STATES[1]:
        greeting(message, user)
    elif user.state == USER_STATES[2]:
        get_ready_to_play(message, user)
    elif user.state == USER_STATES[3]:
        get_category(message, user)
    elif user.state == USER_STATES[4]:
        get_difficulty(message, user)
    elif user.state == USER_STATES[5]:
        get_question(message, user)


def prepare_user(message):
    """
    Prepares user, if he has entered chat for the first time
    :param message:
    :return: User object with name
    """
    user_id = message.from_user.id
    name = message.from_user.first_name
    user = User(id=user_id, state=USER_STATES[0], name=name)
    pinned = bot.send_message(message.chat.id, 'Чат бот для квиза!')
    bot.pin_chat_message(message.chat.id, pinned.id)
    user.state = USER_STATES[1]
    USERS.update({user_id: user})
    return user


def greeting(message, user):
    """
    Greets user and offers to start a game
    :param user: User object
    :param message:
    :return:
    """
    if message.text == '/start':
        bot.send_message(message.chat.id, 'Здравствуйте, ' + message.from_user.first_name + '!')
        bot.send_message(message.chat.id, 'Хотите начать игру?')
        user.state = USER_STATES[2]
    else:
        bot.reply_to(message, 'Введите /start для начала.')


def get_ready_to_play(message, user):
    """
    Asks user if he wants to play, if so - gets token and shows categories
    :param message:
    :param user:
    :return:
    """
    if message.text.lower() == 'да':
        bot.reply_to(message, 'Начинаем!')
        try:
            user.token = get_token()
        except QuizAPIException:
            bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
            raise
        show_categories(message)
        user.state = USER_STATES[3]
    elif message.text.lower() == 'нет':
        bot.reply_to(message, 'Всего доброго!')
        user.state = USER_STATES[0]
    else:
        bot.reply_to(message, 'Не понимаю.')
        bot.send_message(message.chat.id, 'Хотите начать игру? Ответьте да/нет.')


def show_categories(message, sub_cat=False):
    """
    Helper function to show categories
    :param message:
    :param sub_cat: whether we are dealing with nested category
    :return:
    """
    categories = CATEGORIES if not sub_cat else SUB_CATEGORIES[sub_cat]
    markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
    buttons = []
    for cat, i in zip(categories, range(len(categories))):
        locals()['btn' + str(i)] = types.KeyboardButton(cat)
        buttons.append(locals()['btn' + str(i)])
    markup.add(*buttons)
    if sub_cat:
        bot.send_message(message.chat.id, 'Выберите подкатегорию:\n', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Выберите категорию:\n', reply_markup=markup)


def get_category(message, user):
    """
    Getting category from user, checking whether it has subcategory
    :param message:
    :param user:
    :return:
    """
    if message.text.lower() in NESTED_CATEGORIES:
        show_categories(message, sub_cat=message.text.lower())
        user.sub_category = message.text.lower()
    elif message.text in CATEGORIES + SUB_NAMES:
        sub = None if message.text in CATEGORIES else message.text
        category_name = message.text if not sub else user.sub_category.capitalize() + ': ' + message.text
        category_id = get_category_id_by_name(category_name, ALL_CATEGORIES)
        user.current_category = category_id
        bot.reply_to(message, 'Вы выбрали категорию ' + category_name + '.')
        user.state = USER_STATES[4]
        process_difficulty(message)
    else:
        bot.reply_to(message, 'Не понимаю.')


def process_difficulty(message):
    """
    Helper function for showing available difficulty levels
    :param message:
    :return:
    """
    markup = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
    buttons = []
    for diff, i in zip(DIFFICULTY_LEVELS, range(len(DIFFICULTY_LEVELS))):
        locals()['btn' + str(i)] = types.KeyboardButton(diff)
        buttons.append(locals()['btn' + str(i)])
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Выберите сложность:\n', reply_markup=markup)


def get_difficulty(message, user):
    """
    Getting difficulty level from user
    :param message:
    :param user:
    :return:
    """
    if message.text.lower() in DIFFICULTY_LEVELS:
        user.current_difficulty = message.text.lower()
        try:
            question = ask_question(user.token, str(user.current_category), message.text.lower())
        except GetTokenException:
            bot.send_message(message.chat.id, 'Обновляем для вас токен внешнего сервиса, попробуйте еще раз.')
            try:
                user.token = get_token()
            except QuizAPIException:
                bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
                raise
        except QuizAPIException:
            bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
            raise
        else:
            user.current_question = question
            user.state = USER_STATES[5]
            process_question(message, question)
    else:
        bot.reply_to(message, 'Не понимаю.')


def process_question(message, question):
    """
    Helper function to show answers for given question
    :param message:
    :param question:
    :return:
    """
    answers = question.incorrect_answers + [question.correct_answer]
    answers = [html.unescape(item) for item in answers]
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = []
    for answer, i in zip(answers, range(len(answers))):
        locals()['btn' + str(i)] = types.KeyboardButton(answer)
        buttons.append(locals()['btn' + str(i)])
    markup.add(*buttons)
    bot.send_message(message.chat.id, html.unescape(question.question), reply_markup=markup)


def get_question(message, user):
    """
    Getting answer for the question and processing it
    :param message:
    :param user:
    :return:
    """
    question = user.current_question
    escaped_answers = [html.unescape(item) for item in question.incorrect_answers]
    if message.text == html.unescape(question.correct_answer):
        bot.reply_to(message, 'Верно!')
        user.correct_answers += 1
        bot.send_message(message.chat.id, 'Количество правильных ответов: ' + str(user.correct_answers) + '.')
        if user.correct_answers == 5:
            bot.send_sticker(message.chat.id, STICKER_5_ID)
        if user.correct_answers == 10:
            bot.send_sticker(message.chat.id, STICKER_10_ID)
        try:
            question_new = ask_question(
                user.token, str(get_category_id_by_name(question.category, ALL_CATEGORIES)), user.current_difficulty)
        except GetTokenException:
            bot.send_message(message.chat.id, 'Обновляем для вас токен внешнего сервиса, попробуйте еще раз.')
            try:
                user.token = get_token()
            except QuizAPIException:
                bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
                raise
        except QuizAPIException:
            bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
            raise
        else:
            user.current_question = question_new
            process_question(message, question_new)
    elif message.text in escaped_answers:
        user.incorrect_answers += 1
        if question.type == 'boolean':
            bot.reply_to(message, 'Увы, неверно.')
        else:
            bot.reply_to(message, 'Увы, неверно. Правильный ответ ' + html.unescape(question.correct_answer) + '.')
        try:
            question_new = ask_question(
                user.token, str(get_category_id_by_name(question.category, ALL_CATEGORIES)), user.current_difficulty)
        except GetTokenException:
            bot.send_message(message.chat.id, 'Обновляем для вас токен внешнего сервиса, попробуйте еще раз.')
            try:
                user.token = get_token()
            except QuizAPIException:
                bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
                raise
        except QuizAPIException:
            bot.send_message(message.chat.id, 'Проблема с внешним сервисом :(. Попробуйте позже.')
            raise
        else:
            user.current_question = question_new
            process_question(message, question_new)
    else:
        bot.reply_to(message, 'Не понимаю.')


bot.infinity_polling()
