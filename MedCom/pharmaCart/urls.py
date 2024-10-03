from django.urls import path

from . import views

urlpatterns = [
    path('',views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('prescription/', views.prescription, name="prescription"),


    path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
]