from django.contrib import admin
from .models import Thing, Top, ThingInTop, Category, ThingInCategory

admin.site.register(Thing)
admin.site.register(Top)
admin.site.register(ThingInTop)
admin.site.register(Category)
admin.site.register(ThingInCategory)
