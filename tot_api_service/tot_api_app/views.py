from django.db.models import F
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from math import pow, floor
import json
from .models import Thing, Top, ThingInTop, Category, ThingInCategory
from .serializers import (
    ThingSerializer, TopSerializer, ThingInTopSerializer, CategorySerializer,
    AddThingRequestSerializer, BattleRequestSerializer,
    NewThingSerializer, NewCategorySerializer
)

def calculate_elo(thing_a, thing_b, result):
    """
    Рассчитывает новые рейтинги по формуле Эло.
    result: 'win_a' или 'win_b' (пока без ничьей)
    Возвращает (new_rating_a, new_rating_b, delta_a, delta_b, k_a, k_b)
    """
    if result == 'win_a':
        s_a, s_b = 1.0, 0.0
    else:  # 'win_b'
        s_a, s_b = 0.0, 1.0

    e_a = 1 / (1 + pow(10, (thing_b.rating - thing_a.rating) / 400))
    e_b = 1 - e_a

    def get_k_factor(thing):
        if thing.battles_number < 30:
            return 40
        elif thing.rating < 2400:
            return 20
        return 10

    k_a = get_k_factor(thing_a)
    k_b = get_k_factor(thing_b)

    delta_a = k_a * (s_a - e_a)
    delta_b = k_b * (s_b - e_b)

    new_rating_a = thing_a.rating + delta_a
    new_rating_b = thing_b.rating + delta_b

    return new_rating_a, new_rating_b, delta_a, delta_b, k_a, k_b

@api_view(['GET'])
def get_global_top(request):
    """
    Возвращает глобальный топ вещей
    """
    things = Thing.objects.filter(verified=1).order_by('-rating')[:100]
    serializer = ThingSerializer(things, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

@api_view(['GET'])
def get_local_top(request, chat_id):
    """
    Возвращает один локальный топ по его chat_id
    """
    try:
        top = Top.objects.get(chat_id=chat_id)
        
        things_in_top = ThingInTop.objects.filter(chat=top).select_related('thing').order_by('position')
        
        things_list = []
        for item in things_in_top:
            thing = item.thing
            things_list.append({
                'thing_id': thing.thing_id,
                'title': thing.title,
                'position': item.position,
                'rating': thing.rating,
                'battles_number': thing.battles_number,
                'verified': thing.verified
            })
        
        return Response({
            'success': True,
            'data': {
                'chat_id': top.chat_id,
                'voters_number': top.voters_number,
                'left': top.left,
                'right': top.right,
                'cur_index': top.cur_index,
                'new_thing': top.new_thing,
                'votes': top.votes,
                'things': things_list,
                'total_things': len(things_list)
            }
        })
        
    except Top.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Top with chat_id {chat_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_tops(request):
    """
    Все локальные топы
    """
    tops = Top.objects.all()
    serializer = TopSerializer(tops, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

@api_view(['GET'])
def get_things(request):
    """
    Возвращает список всех вещей
    """
    things = Thing.objects.all().order_by('-rating')
    serializer = ThingSerializer(things, many=True)
    return Response({
        'success': True,
        'count': things.count(),
        'data': serializer.data
    })

@api_view(['GET'])
def get_categories(request):
    """
    Возвращает список всех категорий
    """
    categories = Category.objects.all().order_by('title')
    serializer = CategorySerializer(categories, many=True)
    return Response({
        'success': True,
        'count': categories.count(),
        'data': serializer.data
    })

@api_view(['POST'])
def add_new_thing(request):
    """
    Добавляет новую вещь в таблицу things
    """
    serializer = NewThingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    title = serializer.validated_data['title']
    
    try:
        if Thing.objects.filter(title=title).exists():
            return Response({
                'success': False,
                'error': 'Thing with this title already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        thing = Thing.objects.create(
            title=title,
            rating=1000,
            verified=0,
            battles_number=0
        )
        
        serializer_response = ThingSerializer(thing)
        return Response({
            'success': True,
            'message': 'Thing created successfully',
            'data': serializer_response.data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_top(request):
    """
    Создаёт новый пустой топ с указанным chat_id.
    Если топ уже существует, возвращает ошибку.
    """
    chat_id = request.data.get('chat_id')
    chat_type = request.data.get('chat_type')

    if not chat_id or not chat_type:
        return Response({
            'success': False,
            'error': 'chat_id and chat_type are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if Top.objects.filter(chat_id=chat_id).exists():
        return Response({
            'success': False,
            'error': f'Top with chat_id {chat_id} already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Устанавливаем voters_number в зависимости от типа чата
    voters_number = 1 if chat_type == 'private' else 3

    top = Top.objects.create(chat_id=chat_id, voters_number=voters_number)
    serializer = TopSerializer(top)
    return Response({
        'success': True,
        'message': 'Top created successfully',
        'data': serializer.data
    })

@api_view(['POST'])
def add_new_category(request):
    """
    Добавляет новую категорию
    """
    serializer = NewCategorySerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    title = serializer.validated_data['title']
    
    try:
        if Category.objects.filter(title=title).exists():
            return Response({
                'success': False,
                'error': 'Category with this title already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        category = Category.objects.create(title=title)
        
        serializer_response = CategorySerializer(category)
        return Response({
            'success': True,
            'message': 'Category created successfully',
            'data': serializer_response.data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def add_thing_to_top(request):
    """
    Добавляет вещь в топ на указанную позицию
    Если вещи не существует - создаёт её
    """
    serializer = AddThingRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    thing_title = serializer.validated_data['thing_title']
    top_id = serializer.validated_data['top_id']
    position = serializer.validated_data['position']
    
    try:
        with transaction.atomic():
            thing, created = Thing.objects.get_or_create(
                title=thing_title,
                defaults={
                    'rating': 1000,
                    'verified': 0,
                    'battles_number': 0
                }
            )
            
            top, top_created = Top.objects.get_or_create(chat_id=top_id)
            
            if ThingInTop.objects.filter(thing=thing, chat=top).exists():
                return Response({
                    'success': False,
                    'error': 'Thing already exists in this top'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            ThingInTop.objects.create(
                thing=thing,
                chat=top,
                position=position
            )
            
            return Response({
                'success': True,
                'message': 'Thing added to top successfully',
                'thing_created': created,
                'top_created': top_created,
                'thing_id': thing.thing_id,
                'thing_title': thing.title,
                'top_id': top.chat_id
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def handle_battle(request):
    serializer = BattleRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    thing_a_id = serializer.validated_data['thing_a_id']
    thing_b_id = serializer.validated_data['thing_b_id']
    result = serializer.validated_data['result']

    try:
        with transaction.atomic():
            thing_a = Thing.objects.select_for_update().get(thing_id=thing_a_id)
            thing_b = Thing.objects.select_for_update().get(thing_id=thing_b_id)

            old_rating_a = thing_a.rating
            old_rating_b = thing_b.rating
            old_battles_a = thing_a.battles_number
            old_battles_b = thing_b.battles_number

            new_r_a, new_r_b, _, _, _, _ = calculate_elo(thing_a, thing_b, result)

            thing_a.rating = new_r_a
            thing_a.battles_number += 1
            thing_b.rating = new_r_b
            thing_b.battles_number += 1

            thing_a.save()
            thing_b.save()

        return Response({
            'success': True,
            'message': 'Battle results processed',
            'thing_a': {
                'id': thing_a.thing_id,
                'title': thing_a.title,
                'old_rating': old_rating_a,
                'new_rating': thing_a.rating,
                'rating_change': thing_a.rating - old_rating_a,
                'battles_number': thing_a.battles_number
            },
            'thing_b': {
                'id': thing_b.thing_id,
                'title': thing_b.title,
                'old_rating': old_rating_b,
                'new_rating': thing_b.rating,
                'rating_change': thing_b.rating - old_rating_b,
                'battles_number': thing_b.battles_number
            }
        })

    except Thing.DoesNotExist:
        return Response({
            'success': False,
            'error': 'One or both things not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def start_voting(request):
    chat_id = request.data.get('chat_id')
    new_thing_title = request.data.get('new_thing_title')

    if not chat_id or not new_thing_title:
        return Response({
            'success': False,
            'error': 'chat_id and new_thing_title are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        top = Top.objects.get(chat_id=chat_id)
    except Top.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Top with chat_id {chat_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if top.new_thing is not None:
        return Response({
            'success': False,
            'error': 'Voting is already in progress'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Создаём или получаем вещь
    thing, created = Thing.objects.get_or_create(
        title=new_thing_title,
        defaults={'rating': 1000, 'verified': 0, 'battles_number': 0}
    )

    things_in_top = ThingInTop.objects.filter(chat=top).count()

    # Сохраняем информацию о вещи в топе
    top.new_thing = thing.title
    top.new_thing_id = thing.thing_id
    top.new_thing_created = created
    top.left = 0
    top.right = things_in_top
    top.cur_index = floor((0 + things_in_top) / 2) if things_in_top > 0 else 0
    top.votes = json.dumps({})
    top.save()

    if things_in_top == 0:
        # Топ пуст – добавляем вещь сразу
        ThingInTop.objects.create(thing=thing, chat=top, position=1)
        # Сбрасываем состояние голосования
        top.new_thing = None
        top.new_thing_id = None
        top.new_thing_created = False
        top.left = None
        top.right = None
        top.cur_index = None
        top.votes = None
        top.save()
        return Response({
            'success': True,
            'message': 'Top was empty, thing added immediately',
            'position': 1,
            'thing_id': thing.thing_id
        })

    opponent_thing = ThingInTop.objects.filter(chat=top, position=top.cur_index + 1).select_related('thing').first()
    opponent_title = opponent_thing.thing.title if opponent_thing else None

    return Response({
        'success': True,
        'message': 'Voting started',
        'new_thing': top.new_thing,
        'opponent': opponent_title,
        'left': top.left,
        'right': top.right,
        'cur_index': top.cur_index
    })


@api_view(['POST'])
def vote(request):
    chat_id = request.data.get('chat_id')
    user_id = str(request.data.get('user_id'))
    choice = request.data.get('choice')

    if not all([chat_id, user_id, choice]) or choice not in (1, 2):
        return Response({
            'success': False,
            'error': 'chat_id, user_id and choice (1 or 2) are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        top = Top.objects.get(chat_id=chat_id)
    except Top.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Top with chat_id {chat_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if top.new_thing is None:
        return Response({
            'success': False,
            'error': 'No active voting'
        }, status=status.HTTP_400_BAD_REQUEST)

    votes = top.get_votes() if hasattr(top, 'get_votes') else json.loads(top.votes or '{}')

    if user_id in votes:
        return Response({
            'success': False,
            'error': f'User {user_id} has already voted'
        }, status=status.HTTP_400_BAD_REQUEST)

    votes[user_id] = choice
    top.votes = json.dumps(votes)
    top.save()

    total_votes = len(votes)
    votes_for_1 = list(votes.values()).count(1)
    votes_for_2 = list(votes.values()).count(2)
    required = top.voters_number // 2 + 1

    battle_finished = False
    winner = None
    if votes_for_1 >= required:
        battle_finished = True
        winner = 1
    elif votes_for_2 >= required:
        battle_finished = True
        winner = 2

    opponent_thing = ThingInTop.objects.filter(chat=top, position=top.cur_index + 1).select_related('thing').first()
    opponent_title = opponent_thing.thing.title if opponent_thing else None

    if not battle_finished:
        return Response({
            'success': True,
            'message': 'Vote registered',
            'battle_finished': False,
            'votes': votes,
            'new_thing': top.new_thing,
            'opponent': opponent_title
        })

    # --- Батл завершён, обновляем рейтинги ---
    new_thing = Thing.objects.get(thing_id=top.new_thing_id)
    opponent = opponent_thing.thing

    battle_result = 'win_a' if winner == 1 else 'win_b'

    with transaction.atomic():
        # Блокируем записи и обновляем рейтинги
        locked_new = Thing.objects.select_for_update().get(pk=new_thing.pk)
        locked_opp = Thing.objects.select_for_update().get(pk=opponent.pk)
        new_r_a, new_r_b, _, _, _, _ = calculate_elo(locked_new, locked_opp, battle_result)
        locked_new.rating = new_r_a
        locked_new.battles_number += 1
        locked_opp.rating = new_r_b
        locked_opp.battles_number += 1
        locked_new.save()
        locked_opp.save()
    # -----------------------------------------

    # Обновляем границы и очищаем голоса
    if winner == 1:
        top.right = top.cur_index
    else:
        top.left = top.cur_index + 1

    top.votes = json.dumps({})
    top.save()

    # Проверяем, завершено ли голосование
    if top.left >= top.right:
        position = top.left + 1
        # Используем уже существующую вещь (new_thing)
        ThingInTop.objects.create(thing=new_thing, chat=top, position=position)

        # Сбрасываем состояние голосования
        top.new_thing = None
        top.new_thing_id = None
        top.new_thing_created = False
        top.left = None
        top.right = None
        top.cur_index = None
        top.votes = None
        top.save()

        return Response({
            'success': True,
            'message': 'Voting finished, thing added',
            'battle_finished': True,
            'voting_finished': True,
            'winner': winner,
            'position': position,
            'thing_id': new_thing.thing_id,
            'new_thing': new_thing.title  # передаём название для бота
        })

    # Голосование продолжается – вычисляем следующий индекс
    top.cur_index = floor((top.left + top.right) / 2)
    top.save()

    new_opponent = ThingInTop.objects.filter(chat=top, position=top.cur_index + 1).select_related('thing').first()
    new_opponent_title = new_opponent.thing.title if new_opponent else None

    return Response({
        'success': True,
        'message': 'Battle finished, next round',
        'battle_finished': True,
        'voting_finished': False,
        'winner': winner,
        'new_opponent': new_opponent_title,
        'left': top.left,
        'right': top.right,
        'cur_index': top.cur_index,
        'new_thing': top.new_thing  # тоже полезно
    })

@api_view(['POST'])
def cancel_voting(request):
    chat_id = request.data.get('chat_id')

    if not chat_id:
        return Response({
            'success': False,
            'error': 'chat_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        top = Top.objects.get(chat_id=chat_id)
    except Top.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Top with chat_id {chat_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if top.new_thing is None:
        return Response({
            'success': False,
            'error': 'No active voting to cancel'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Удаляем вещь, только если она была создана в этом голосовании
    if top.new_thing_created and top.new_thing_id:
        Thing.objects.filter(thing_id=top.new_thing_id).delete()

    # Сбрасываем все поля голосования
    top.new_thing = None
    top.new_thing_id = None
    top.new_thing_created = False
    top.left = None
    top.right = None
    top.cur_index = None
    top.votes = None
    top.save()

    return Response({
        'success': True,
        'message': 'Voting cancelled and thing deleted if newly created'
    })


@api_view(['POST'])
def cancel_vote(request):
    """
    Удаляет голос конкретного пользователя.
    Ожидает: {"chat_id": "...", "user_id": "..."}
    """
    chat_id = request.data.get('chat_id')
    user_id = str(request.data.get('user_id'))

    if not chat_id or not user_id:
        return Response({
            'success': False,
            'error': 'chat_id and user_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        top = Top.objects.get(chat_id=chat_id)
    except Top.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Top with chat_id {chat_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if top.new_thing is None:
        return Response({
            'success': False,
            'error': 'No active voting'
        }, status=status.HTTP_400_BAD_REQUEST)

    votes = top.get_votes() if hasattr(top, 'get_votes') else json.loads(top.votes or '{}')

    if user_id not in votes:
        return Response({
            'success': False,
            'error': f'User {user_id} has not voted'
        }, status=status.HTTP_400_BAD_REQUEST)

    del votes[user_id]
    top.votes = json.dumps(votes)
    top.save()

    return Response({
        'success': True,
        'message': 'Vote cancelled',
        'votes': votes
    })

from django.shortcuts import render

def home_page(request):
    """
    Главная страница с глобальным топом
    """
    things = Thing.objects.filter(verified=1).order_by('-rating')
    
    context = {
        'things': things
    }
    
    return render(request, 'global_top.html', context)