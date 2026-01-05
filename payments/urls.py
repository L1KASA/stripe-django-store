from django.urls import path
from . import views

urlpatterns = [
    path('order/intent/<int:order_id>/', views.create_order_payment_intent, name='create_order_payment_intent'),
    path('checkout/<int:item_id>/', views.create_order_direct, name='create_order_direct'),
    path('payment/<int:order_id>/', views.order_payment, name='order_payment'),
    path('order/session/<int:order_id>/', views.create_order_checkout_session, name='create_order_checkout_session'),
    path('', views.payment_success, name='success'),
]
