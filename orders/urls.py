from django.urls import path
from . import views

urlpatterns = [
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('create/<int:item_id>/', views.create_order, name='create_order'),
    path('order/<int:order_id>/discount/', views.apply_discount, name='apply_discount'),
    path('clear/', views.clear_new_order, name='clear_new_order'),
]
