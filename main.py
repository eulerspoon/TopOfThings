import telebot
from top import Top
from resourses import filepath, TOKEN, greeting, commands_list

bot = telebot.TeleBot(TOKEN)

top = Top(filepath)

votes = {}
people_in_club = 3 # needs to be odd yet
voting_in_progress = False
left = 0
right = top.size - 1
cur_index = None
thing = None

@bot.message_handler(commands=['start'])
def greet(message):
    bot.send_message(message.chat.id, greeting)


@bot.message_handler(commands=['add'])
def add_thing(message):
    global votes
    global thing
    global votes
    global voting_in_progress
    global cur_index
    splited = message.text.split()
    answer = ""
    if len(splited) != 2:
        bot.send_message(message.chat.id, "Неверный формат команды add.", reply_to_message_id=message.message_id)
        return
    thing = splited[1]
    thing = thing[0].upper() + thing[1:].lower()
    answer += "Перезапускаю голосование.\nЧто лучше?\n\n" if voting_in_progress else "Запускаю голосование.\nЧто лучше?\n\n"
    votes = {}
    voting_in_progress = True
    cur_index = (left + right) // 2
    answer += f"1. {thing}\n2. {top.things[cur_index]}"
    
    bot.send_message(message.chat.id, answer)
    

@bot.message_handler(commands=['vote'])
def vote_for_thing(message):
    global votes
    global thing
    global votes
    global voting_in_progress
    global cur_index
    global right
    global left
    if len(message.text.split()) != 2 or message.text[-1] not in ('1', '2'):
        bot.send_message(message.chat.id, "Неверный формат команды vote.", reply_to_message_id=message.message_id)
        return
    user_id = message.from_user.id
    if not voting_in_progress or user_id in votes: return
    if not voting_in_progress: return
    vote = int(message.text[-1])
    votes[user_id] = vote
    if len(votes) != people_in_club: return
    
    winner = max(votes.values(), key=list(votes.values()).count)
    if winner == 1:
        right = cur_index - 1
    else:
        left = cur_index + 1
    if left >= right:
        top.add(thing, left)
        bot.send_message(message.chat.id, f'Голосование завершено. ' + '\n' + f'Добавил {thing} на позицию {left + 1}.')
        votes = {}
        vote_in_progress = False
        left = 1
        right = top.size
        return
    cur_index = (left + right) // 2
    bot.send_message(message.chat.id, 'Что лучше?\n\n' + f'1. {thing}' + '\n' + f'2. {top.things[cur_index]}')
    votes = {}
    

@bot.message_handler(commands=['help'])
def print_help(message):
    bot.send_message(message.chat.id, commands_list)


@bot.message_handler(commands=['top'])
def print_top(message):
    try:
        top_number = int(message.text.split()[1]) if message.text.strip() != '/top' else top.size
        answer = ""
        for i in range(min(top_number, top.size)):
            answer += f"{i + 1}. {top.things[i]}" + '\n'
        bot.send_message(message.chat.id, answer)
    except:
        bot.send_message(message.chat.id, "Неверный формат команды top.", reply_to_message_id=message.message_id)


@bot.message_handler(commands=['get_txt'])
def send_txt(message):
    bot.send_document(chat_id=message.chat.id, document=open(filepath))


bot.polling()

