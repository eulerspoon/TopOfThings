from django.contrib import admin
from django.urls import path, include
from tot_api_app.views import home_page

urlpatterns = [
    path('', home_page, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('tot_api_app.urls')),
]