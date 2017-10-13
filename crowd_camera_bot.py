import telebot
import requests
import threading
from crowd_checker import CrowdChecker
from strings import bus_timetable_message, bus_stops_message, medical_message
from utils import subscribe_chat_id, unsubscribe_chat_id
from utils import get_bus_markup, get_default_markup

TOKEN = "TOKEN"
CROWD_THRESHOLD = 10
bot = telebot.TeleBot(TOKEN)
crowdChecker = CrowdChecker()
crowdChecker.start()

current_context = {'subscribed_chats': set()}

def callback_minute():
    for chat_id in current_context['subscribed_chats']:
        amount = crowdChecker.howManyPeopleNow()
        if amount > CROWD_THRESHOLD:
            bot.send_message(chat_id=chat_id,
            text='ВНИМАНИЕ: на остановке много людей. \
В данный момент количество: *{}*\n\
Советуем дождаться следующего автобуса\n\
_Вы были автоматически отписаны от уведомлений.\n\
Для повторной подписки нажмите "Подписаться на уведомления"_'.format(amount),
            parse_mode='MARKDOWN')
            unsubscribe_chat_id(chat_id)
    threading.Timer(60, callback_minute).start()

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        current_chat_id = call.message.chat.id

        if call.data == "people_count":
            send_text = "Людей на остановке сейчас: *{}*".format(crowdChecker.howManyPeopleNow())

        if call.data == "subscribe":
            send_text = "Вы успешно подписались на уведомления!"
            subscribe_chat_id(current_context, current_chat_id)

        if call.data == "unsubscribe":
            send_text = "Вы успешно отписались от уведомлений!"
            unsubscribe_chat_id(current_context, current_chat_id)

        if call.data == 'timetable':
            send_text = bus_timetable_message()

        if call.data == 'bus_stops':
            send_text = bus_stops_message()

        if call.data == 'where_is_bus':
            send_text = '_Скоро будет реализовано._'

        if call.data == 'no_space':
            send_text = '_Ваш отзыв принят._'

        if call.data in ['people_count', 'subscribe', 'unsubscribe',
                         'timetable', 'bus_stops', 'where_is_bus',
                         'no_space']:
            s = requests.Session()
            s.get('https://api.telegram.org/bot{0}/deletemessage?message_id={1}&chat_id={2}'.format( \
            TOKEN, call.message.message_id, current_chat_id))
            bot.send_message(chat_id=current_chat_id,
                text=send_text, parse_mode='MARKDOWN',
                reply_markup=get_bus_markup(current_context, current_chat_id))


@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    bot.send_message(chat_id=message.chat.id,
                    text='Привет, {}!\n\
Я клон бота-справочника о городе Иннополис!😉 \n\nЕсли ты не нашел \
нужной информации, то можешь позвонить в Консьерж-сервис:\n\
☎️: 8-800-222-22-87\n\
📩: helpme@innopolis.ru\n\
telegram: @InnopolisHelp!'.format(message.from_user.first_name),
                    parse_mode='MARKDOWN', reply_markup=get_default_markup())

@bot.message_handler(func=lambda x: x not in ['/start', '/help'])
def handle_all(message):
    current_chat_id = message.chat.id
    markup = get_default_markup()
    if message.text == '🚌':
        text = "Актуальное расписание движения автобусов (⌛️) и информация по остановкам (🏁)"
        markup = get_bus_markup(current_context, current_chat_id)
    elif message.text == '🚑':
        text = medical_message()
    elif message.text == '🏠':
        text = "Здесь будет режим работы и контактные телефоны учреждений в нашем городе"
    elif message.text == '👤':
        text = "Разработчики бота: @lemhell, @vladvin.\nСпециально для Arch City Hack"
    else:
        text = "Не очень понял запрос"
    bot.send_message(chat_id=current_chat_id,
                    text=text, reply_markup=markup, parse_mode='MARKDOWN')


callback_minute()
bot.polling(none_stop=False, interval=0, timeout=40)

crowdChecker.join()
