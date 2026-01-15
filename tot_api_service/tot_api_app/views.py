from django.db.models import F
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from math import pow
from .models import Thing, Top, ThingInTop, Category, ThingInCategory
from .serializers import (
    ThingSerializer, TopSerializer, ThingInTopSerializer, CategorySerializer,
    AddThingRequestSerializer, BattleRequestSerializer,
    NewThingSerializer, NewCategorySerializer
)

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
def get_tops(request):
    """
    Возвращает локальный топ вещей по id
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
    """
    Обрабатывает результат батла и обновляет рейтинги вещей
    """
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
            
            if result == 'win_a':
                s_a = 1.0
                s_b = 0.0
            elif result == 'win_b':
                s_a = 0.0
                s_b = 1.0
            else:
                s_a = 0.5
                s_b = 0.5
            
            e_a = 1 / (1 + pow(10, (thing_b.rating - thing_a.rating) / 400))
            e_b = 1 - e_a
            
            def get_k_factor(thing):
                if thing.battles_number < 30:
                    return 40
                elif thing.rating < 2400:
                    return 20
                else:
                    return 10
            
            k_a = get_k_factor(thing_a)
            k_b = get_k_factor(thing_b)
            
            new_rating_a = thing_a.rating + k_a * (s_a - e_a)
            new_rating_b = thing_b.rating + k_b * (s_b - e_b)
            
            old_rating_a = thing_a.rating
            old_rating_b = thing_b.rating
            
            thing_a.rating = new_rating_a
            thing_a.battles_number = F('battles_number') + 1
            thing_a.save()
            
            thing_b.rating = new_rating_b
            thing_b.battles_number = F('battles_number') + 1
            thing_b.save()
            
            thing_a.refresh_from_db()
            thing_b.refresh_from_db()
            
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