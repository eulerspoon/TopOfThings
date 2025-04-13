class Voting:
    def __init__(self, top_size, voters_number):
        self.top_size = top_size
        self.on()
        self.voters_number = voters_number
        self.in_progress = False

    def vote(self, user_id, option):
        if user_id not in self.votes:
            self.votes[user_id] = option

    def is_over(self):
        values = list(self.votes.values())
        return values.count(1) > self.voters_number // 2 or values.count(2) > self.voters_number // 2

    def result(self):
        return max((1, 2), key=list(self.votes.values()).count)

    def get_state(self):
        result = self.new_thing + ' - ' + str(list(self.votes.values()).count(1)) + '\n'
        result += self.old_thing + ' - ' + str(list(self.votes.values()).count(2))
        return result

    def on(self):
        self.in_progress = True
        self.left = 0
        self.right = self.top_size
        self.cur_index = None
        self.new_thing = None
        self.old_thing = None
        self.votes = {}

    def off(self):
        self.in_progress = False

    def next_step(self, things):
        self.cur_index = (self.left + self.right) // 2
        self.old_thing = things[self.cur_index]
        self.votes = {}
        self.in_progress = True

    def get_vote_ask(self):
        result = '\nЧто лучше?\n\n'
        result += f"1. {self.new_thing}\n"
        result += f"2. {self.old_thing}"
        return result
