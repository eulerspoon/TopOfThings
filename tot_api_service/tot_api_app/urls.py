from django.urls import path
from . import views

urlpatterns = [
    path('global_top/', views.get_global_top, name='get_global_top'),
    path('things/', views.get_things, name='get_things'),
    path('categories/', views.get_categories, name='get_categories'),
    path('tops/', views.get_tops, name='get_tops'),
    path('add_new_thing/', views.add_new_thing, name='add_new_thing'),
    path('add_new_category/', views.add_new_category, name='add_new_category'),
    path('add_thing_to_top/', views.add_thing_to_top, name='add_thing_to_top'),
    path('handle_battle/', views.handle_battle, name='handle_battle'),
]
