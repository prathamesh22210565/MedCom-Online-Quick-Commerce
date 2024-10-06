from django.urls import path

from . import views

urlpatterns = [
    path('',views.store, name="store"),
    path('cart/', views.cart, name="cart"),
    path('checkout/', views.checkout, name="checkout"),
    path('prescription/', views.prescription, name="prescription"),
    path('upload-image/', views.upload_image, name='upload_image'),
    path('upload_image_to_ngrok/', views.upload_image_to_ngrok, name='upload_image_to_ngrok'),
    path('upload_image_to_flask/', views.upload_image_to_flask, name="upload_image_to_flask"),

    path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
]