from telebot import types

def subscribe_chat_id(current_context, chat_id):
    subscribed_set = current_context['subscribed_chats']
    subscribed_set.add(chat_id)
    current_context['subscribed_chats'] = subscribed_set

def unsubscribe_chat_id(current_context, chat_id):
    subscribed_set = current_context['subscribed_chats']
    if chat_id in subscribed_set:
        subscribed_set.remove(chat_id)
        current_context['subscribed_chats'] = subscribed_set

# markups

def get_default_markup():
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    markup.add(types.KeyboardButton('🚌'),
               types.KeyboardButton('🚑'),
               types.KeyboardButton('🏠'),
               types.KeyboardButton('👤'))
    return markup

def get_bus_markup(current_context, chat_id):
    keyboard = types.InlineKeyboardMarkup()
    button_list = [
        types.InlineKeyboardButton("Сколько людей на остановке? 🤔", callback_data='1'),
        types.InlineKeyboardButton("Подписаться на уведомления", callback_data='1.sub'),
        types.InlineKeyboardButton("⌛️ 'Комбинат Здоровье'", callback_data='2'),
         types.InlineKeyboardButton("🏁 'Комбинат Здоровье'", callback_data='3'),
         types.InlineKeyboardButton("❓ Где мой автобус?!", callback_data='4'),
         types.InlineKeyboardButton("🆘 Не хватило места", callback_data='5')
    ]
    if chat_id in current_context['subscribed_chats']:
        button_list[1] = types.InlineKeyboardButton("Отписаться от уведомлений", callback_data='1.unsub')

    [keyboard.add(callback_button) for callback_button in button_list]
    return keyboard
