from rest_framework import serializers
from .models import Thing, Top, ThingInTop, Category, ThingInCategory

class ThingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thing
        fields = ['thing_id', 'title', 'rating', 'verified', 'battles_number']

class TopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Top
        fields = ['chat_id', 'voters_number', 'left', 'right', 'cur_index', 'new_thing', 'votes']

class ThingInTopSerializer(serializers.ModelSerializer):
    thing_title = serializers.CharField(source='thing.title', read_only=True)
    
    class Meta:
        model = ThingInTop
        fields = ['thing', 'thing_title', 'chat', 'position']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']

class AddThingRequestSerializer(serializers.Serializer):
    thing_title = serializers.CharField(max_length=255)
    top_id = serializers.CharField(max_length=255)
    position = serializers.IntegerField(min_value=1)

class BattleRequestSerializer(serializers.Serializer):
    thing_a_id = serializers.IntegerField()
    thing_b_id = serializers.IntegerField()
    result = serializers.ChoiceField(choices=['win_a', 'win_b', 'draw'])

class NewThingSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)

class NewCategorySerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)