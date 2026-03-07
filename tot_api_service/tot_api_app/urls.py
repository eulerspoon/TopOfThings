from django.urls import path
from . import views

urlpatterns = [
    path('global_top/', views.get_global_top, name='get_global_top'),
    path('things/', views.get_things, name='get_things'),
    path('categories/', views.get_categories, name='get_categories'),
    path('tops/', views.get_tops, name='get_tops'),
    path('tops/<str:chat_id>/', views.get_local_top, name='get_local_top'),
    path('create_top/', views.create_top, name='create_top'),
    path('add_new_thing/', views.add_new_thing, name='add_new_thing'),
    path('add_new_category/', views.add_new_category, name='add_new_category'),
    path('add_thing_to_top/', views.add_thing_to_top, name='add_thing_to_top'),
    path('handle_battle/', views.handle_battle, name='handle_battle'),

    path('start_voting/', views.start_voting, name='start_voting'),
    path('vote/', views.vote, name='vote'),
    path('cancel_voting/', views.cancel_voting, name='cancel_voting'),
    path('cancel_vote/', views.cancel_vote, name='cancel_vote'),
]
