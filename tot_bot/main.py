import telebot
import requests
import json
from resources import BOT_TOKEN, API_BASE_URL
from urllib.parse import urljoin

bot = telebot.TeleBot(BOT_TOKEN)

# Вспомогательная функция для вызова API
def api_request(method, endpoint, data=None, params=None):
    url = urljoin(API_BASE_URL, endpoint.lstrip('/'))
    try:
        if method == 'GET':
            response = requests.get(url, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            return None, 'Unsupported method'
        
        if response.status_code == 200:
            return response.json(), None
        else:
            error_msg = f'API error {response.status_code}: {response.text}'
            return None, error_msg
    except requests.exceptions.RequestException as e:
        return None, str(e)

def ensure_top_exists(chat_id, chat_type):
    """Пытается создать топ для чата; если уже существует – ничего не делает."""
    data = {
        'chat_id': chat_id,
        'chat_type': chat_type
    }
    result, error = api_request('POST', 'create_top/', data=data)
    if error:
        print(f"Ошибка при создании топа: {error}")
        return False
    if result.get('success'):
        print(f"Создан новый топ для чата {chat_id}")
        return True
    else:
        # Если топ уже существует, это нормально
        if 'already exists' in result.get('error', ''):
            return True
        print(f"Не удалось создать топ: {result.get('error')}")
        return False

# Команда /start
@bot.message_handler(commands=['start'])
def greet(message):
    chat_id = str(message.chat.id)
    chat_type = message.chat.type
    ensure_top_exists(chat_id, chat_type)  # создаст топ, если его ещё нет
    bot.send_message(chat_id, "Привет! Я люблю сортировать вещи. Используй /help для списка команд.")

# Команда /help
@bot.message_handler(commands=['help'])
def print_help(message):
    help_text = (
        "/add <название> - начать голосование за добавление новой вещи\n"
        "/vote1 или /vote2 - проголосовать за первый или второй вариант\n"
        "/cancel - отменить текущее голосование\n"
        "/unvote - отозвать свой голос\n"
        "/voting - показать текущий статус голосования\n"
        "/top [N] - показать топ вещей (N - количество или диапазон, например 1-5)\n"
    )
    bot.send_message(message.chat.id, help_text)

# Команда /add <название>
@bot.message_handler(commands=['add'])
def add_thing(message):
    chat_id = str(message.chat.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(chat_id, "Укажите название вещи после команды /add")
        return

    new_thing_title = parts[1].strip()
    data = {
        'chat_id': chat_id,
        'new_thing_title': new_thing_title
    }
    result, error = api_request('POST', 'start_voting/', data=data)
    if error:
        bot.send_message(chat_id, f"Ошибка: {error}")
        return

    if result.get('success'):
        if result.get('message') == 'Top was empty, thing added immediately':
            bot.send_message(chat_id, f"Топ пуст, вещь \"{new_thing_title}\" добавлена на позицию {result['position']}.")
        else:
            # Голосование началось
            opponent = result.get('opponent', 'неизвестно')
            bot.send_message(
                chat_id,
                f"\nЧто лучше?\n1. {new_thing_title}\n2. {opponent}\n\nГолосуйте: /vote1 или /vote2"
            )
    else:
        bot.send_message(chat_id, f"Не удалось начать голосование: {result.get('error', 'неизвестная ошибка')}")

# Команда /vote (ожидает аргумент 1 или 2)
@bot.message_handler(commands=['vote'])
def vote(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    parts = message.text.split()
    if len(parts) != 2 or parts[1] not in ('1', '2'):
        bot.send_message(chat_id, "Используйте: /vote1 или /vote2")
        return

    choice = int(parts[1])
    data = {
        'chat_id': chat_id,
        'user_id': user_id,
        'choice': choice
    }
    result, error = api_request('POST', 'vote/', data=data)
    if error:
        bot.send_message(chat_id, f"Ошибка: {error}")
        return

    if not result.get('success'):
        bot.send_message(chat_id, f"Ошибка: {result.get('error', 'неизвестная ошибка')}")
        return

    if result.get('voting_finished'):
        # Голосование завершено, вещь добавлена
        bot.send_message(
            chat_id,
            f"Голосование завершено! Вещь \"{result.get('new_thing', '') if 'new_thing' in result else ''}\" добавлена на позицию {result['position']}."
        )
        show_top(chat_id, limit=5)
    elif result.get('battle_finished'):
        # Батл завершён, но голосование продолжается
        new_opponent = result.get('new_opponent', 'неизвестно')
        bot.send_message(
            chat_id,
            f"\nЧто лучше?\n1. {result.get('new_thing', '')}\n2. {new_opponent}\n\nГолосуйте: /vote1 или /vote2"
        )
    else:
        # Голос принят, но батл ещё не завершён
        # bot.send_message(chat_id, "Ваш голос принят. Ждём остальных участников.")
        pass

@bot.message_handler(commands=['vote1'])
def vote1(message):
    message.text = '/vote 1'
    vote(message)

@bot.message_handler(commands=['vote2'])
def vote2(message):
    message.text = '/vote 2'
    vote(message)

# Команда /cancel - отменить голосование
@bot.message_handler(commands=['cancel'])
def cancel_voting(message):
    chat_id = str(message.chat.id)
    data = {'chat_id': chat_id}
    result, error = api_request('POST', 'cancel_voting/', data=data)
    if error:
        bot.send_message(chat_id, f"Ошибка: {error}")
        return

    if result.get('success'):
        bot.send_message(chat_id, "Голосование отменено.")
    else:
        bot.send_message(chat_id, f"Не удалось отменить: {result.get('error', 'неизвестная ошибка')}")

# Команда /unvote - отозвать свой голос
@bot.message_handler(commands=['unvote'])
def cancel_vote(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    data = {
        'chat_id': chat_id,
        'user_id': user_id
    }
    result, error = api_request('POST', 'cancel_vote/', data=data)
    if error:
        bot.send_message(chat_id, f"Ошибка: {error}")
        return

    if result.get('success'):
        # bot.send_message(chat_id, "Ваш голос удалён.")
        pass
    else:
        bot.send_message(chat_id, f"Не удалось удалить голос: {result.get('error', 'неизвестная ошибка')}")

# Команда /voting - показать статус голосования
@bot.message_handler(commands=['voting'])
def voting_status(message):
    chat_id = str(message.chat.id)
    # Получаем текущий топ с информацией о голосовании
    result, error = api_request('GET', f'tops/{chat_id}/')
    if error:
        bot.send_message(chat_id, f"Ошибка получения статуса: {error}")
        return

    if not result.get('success'):
        bot.send_message(chat_id, f"Не удалось получить информацию: {result.get('error', 'неизвестная ошибка')}")
        return

    data = result.get('data', {})
    new_thing = data.get('new_thing')
    if not new_thing:
        bot.send_message(chat_id, "Сейчас нет активного голосования.")
        return

    # Получаем текущего соперника по cur_index
    things = data.get('things', [])
    cur_index = data.get('cur_index')
    opponent = None
    if cur_index is not None and 0 <= cur_index < len(things):
        opponent = things[cur_index].get('title', 'неизвестно')

    votes_str = data.get('votes', '{}')
    try:
        votes = json.loads(votes_str) if votes_str else {}
    except:
        votes = {}
    voters_number = data.get('voters_number', 1)
    total_votes = len(votes)
    votes_for_1 = list(votes.values()).count(1)
    votes_for_2 = list(votes.values()).count(2)

    status_text = (
        f"Текущее голосование:\n"
        f"1. {new_thing} - {votes_for_1}\n"
        f"2. {opponent} - {votes_for_2}\n"
    )
    bot.send_message(chat_id, status_text)

def show_top(chat_id, limit=None):
    """Показывает топ для указанного chat_id (опционально limit)"""
    result, error = api_request('GET', f'tops/{chat_id}/')
    if error:
        return None, error
    if not result.get('success'):
        return None, result.get('error')
    things = result.get('data', {}).get('things', [])
    # Формируем вывод (можно вернуть список для последующей обработки)
    return things, None

# Команда /top [N] - показать топ вещей
@bot.message_handler(commands=['top'])
def handle_top(message):
    chat_id = str(message.chat.id)
    things, error = show_top(chat_id)
    if error:
        bot.send_message(chat_id, f"Ошибка: {error}")
        return
    if not things:
        bot.send_message(chat_id, "Топ пока пуст.")
        return

    # Обработка аргументов команды (диапазон или количество)
    parts = message.text.split()
    start, end = 1, len(things)  # по умолчанию все
    if len(parts) >= 2:
        arg = parts[1]
        if arg.isdigit():
            # Просто число: показать первые N
            n = int(arg)
            end = min(n, len(things))
        elif '-' in arg:
            # Диапазон, например 3-7
            try:
                a, b = map(int, arg.split('-'))
                if a > b:
                    a, b = b, a
                start = max(1, a)
                end = min(b, len(things))
            except:
                pass

    # Формируем сообщение
    lines = []
    for i in range(start-1, end):
        item = things[i]
        lines.append(f"{i+1}. {item['title']} ({item['rating']:.0f})")
    bot.send_message(chat_id, "\n".join(lines))

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()