from django.db import models
import json

class Thing(models.Model):
    thing_id = models.AutoField(primary_key=True)
    title = models.TextField(unique=True)
    rating = models.FloatField(default=1000)
    verified = models.IntegerField(default=0)  # 1 -> approved; -1 -> declined; 0 -> waiting
    battles_number = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'things'
    
    def __str__(self):
        return f"{self.title} (rating: {self.rating})"


class Top(models.Model):
    chat_id = models.TextField(primary_key=True)
    voters_number = models.IntegerField(default=1)
    left = models.IntegerField(null=True, blank=True)
    right = models.IntegerField(null=True, blank=True)
    cur_index = models.IntegerField(null=True, blank=True)
    new_thing = models.TextField(null=True, blank=True)
    new_thing_id = models.IntegerField(null=True, blank=True)
    new_thing_created = models.BooleanField(default=False)
    votes = models.TextField(null=True, blank=True) # json as text
    
    class Meta:
        db_table = 'tops'
    
    def get_votes(self):
        """Получить votes как словарь"""
        if self.votes:
            return json.loads(self.votes)
        return {}
    
    def set_votes(self, votes_dict):
        """Установить votes из словаря"""
        self.votes = json.dumps(votes_dict)
    
    def __str__(self):
        return f"Top {self.chat_id}"


class Category(models.Model):
    title = models.TextField(unique=True)
    
    class Meta:
        db_table = 'categories'
    
    def __str__(self):
        return self.title


class ThingInCategory(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, db_column='thing_id')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')
    
    class Meta:
        db_table = 'things_in_categories'
        unique_together = (('thing', 'category'),)
    
    def __str__(self):
        return f"{self.thing.title} in {self.category.title}"


class ThingInTop(models.Model):
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, db_column='thing_id')
    chat = models.ForeignKey(Top, on_delete=models.CASCADE, db_column='chat_id')
    position = models.IntegerField()
    
    class Meta:
        db_table = 'things_in_tops'
        unique_together = (('thing', 'chat'),)
    
    def __str__(self):
        return f"{self.thing.title} at position {self.position} in {self.chat.chat_id}"