from .views import item_list
from django.urls import path

app_name = 'store'

urlpatterns = [
    path('', item_list, name='item-list')
]
