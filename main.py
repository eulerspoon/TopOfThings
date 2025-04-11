import telebot
from top import Top
from voting import Voting
from resourses import FILEPATH, TOKEN, GREETING, COMMANDS_LIST

bot = telebot.TeleBot(TOKEN)

top = Top(FILEPATH)

voting = Voting(top.size, voters_number=3)

@bot.message_handler(commands=['start'])
def greet(message):
    bot.send_message(message.chat.id, GREETING)


@bot.message_handler(commands=['add'])
def add_thing(message):
    if voting.in_progress:
        bot.send_message(
            message.chat.id,
            "Сначала нужно закончить предыдущее голосование.",
            reply_to_message_id=message.message_id
        )
        return
    
    splited = message.text.split()
    if len(splited) != 2:
        bot.send_message(
            message.chat.id,
            "Неверный формат команды add.",
            reply_to_message_id=message.message_id
        )
        return

    voting.on()

    voting.new_thing = splited[1][0].upper() + splited[1][1:].lower()

    voting.cur_index = (voting.left + voting.right) // 2
    voting.old_thing = top.things[voting.cur_index]
    
    bot.send_message(message.chat.id, voting.get_vote_ask())
    

@bot.message_handler(commands=['vote'])
def vote_for_thing(message):
    if not voting.in_progress:
        bot.send_message(
            message.chat.id,
            "Сейчас не идёт голосование.",
            reply_to_message_id=message.message_id
        )
        return
    
    splited = message.text.split()
    if len(splited) != 2 or len(splited[1]) != 1 or message.text[-1] not in ('1', '2'):
        bot.send_message(
            message.chat.id,
            "Неверный формат команды vote.",
            reply_to_message_id=message.message_id
        )
        return

    user_id = message.from_user.id
    if user_id in voting.votes:
        bot.send_message(
            message.chat.id,
            f"Ты уже проголосовал за {voting.votes[user_id]}.",
            reply_to_message_id=message.message_id
        )
        return
    
    chose = int(message.text[-1])
    voting.vote(user_id, chose)

    if not voting.is_over():
        bot.send_message(
            message.chat.id,
            voting.get_state(),
            reply_to_message_id=message.message_id
        )
        return

    if voting.result() == 1:
        voting.right = voting.cur_index - 1
    else:
        voting.left = voting.cur_index + 1

    if voting.left >= voting.right:
        top.add(voting.new_thing, voting.left)
        answer = f'Вещь "{voting.new_thing}" добавлена на позицию {voting.left + 1}:\n\n'
        if voting.left != 0:
            answer += '...\n'

        if voting.left == 0:
            start, end = 0, 3
        elif voting.left == top.size - 1:
            start, end = top.size - 3, top.size
        else:
            start, end = voting.left - 1, voting.left + 2

        for i in range(start, end):
            answer += f'{i + 1}. {top.things[i]}'
            if i != end - 1:
                answer += '\n'

        if voting.left != top.size - 1:
            answer += '\n...'

        bot.send_message(
            message.chat.id,
            answer
        )
        voting.off()
        return

    voting.cur_index = (voting.left + voting.right) // 2
    voting.old_thing = top.things[voting.cur_index]
    voting.next_step()

    bot.send_message(message.chat.id, voting.get_vote_ask())
    

@bot.message_handler(commands=['help'])
def print_help(message):
    bot.send_message(message.chat.id, COMMANDS_LIST)


@bot.message_handler(commands=['top'])
def print_top(message):
    splited = message.text.split()
    first_case = len(splited) == 1
    second_case = len(splited) == 2 and splited[1].isdigit()
    second_case = second_case and int(splited[1]) > 0
    third_case = len(splited) == 2 and splited[1].count('-') == 1 
    third_case = third_case and all(x.isdigit() for x in splited[1].split('-'))
    third_case = third_case and splited[1].index('-') not in (0, len(splited[1]) - 1)
    if not (first_case or second_case or third_case):
        bot.send_message(
            message.chat.id,
            "Неверный формат команды top.",
            reply_to_message_id=message.message_id
        )
        return
    if first_case:
        start, end = 0, top.size
    elif second_case:
        start, end = 0, min(int(splited[1]), top.size)
    elif third_case:
        start, end = map(int, splited[1].split('-'))
        if start > end and end != 0: end -= 2
        elif end == 0: end = -1
        if start != 0: start -= 1
    step = 1 if start <= end else -1
    answer = ''
    if step == 1 and end > top.size - 1: end = top.size
    for i in range(start, end, step):
        answer += f'{i + 1}. {top.things[i]}' + '\n'

    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['get_txt'])
def send_txt(message):
    bot.send_document(chat_id=message.chat.id, document=open(FILEPATH))


@bot.message_handler(commands=['voting'])
def send_voting_info(message):
    if voting.in_progress:
        result = voting.get_vote_ask() + '\n\n'
        result += voting.get_state()
    else:
        result = "Сейчас не идёт голосование."
    bot.send_message(
        message.chat.id,
        result,
        reply_to_message_id=message.message_id
    )


@bot.message_handler(commands=['cancel'])
def send_voting_info(message):
    if voting.in_progress:
        voting.off()
        result = "Голосование прекращено."
    else:
        result = "Сейчас не идёт голосование."
    bot.send_message(
        message.chat.id,
        result,
        reply_to_message_id=message.message_id
    )

bot.polling()
