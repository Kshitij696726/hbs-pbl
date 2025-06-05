from django.urls import path
from django.shortcuts import render
from . import views
from django.contrib.auth import views as auth_views

app_name = 'booking'

urlpatterns = [
    path('', lambda request: render(request, 'booking/base.html'), name='welcome'),
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/add/', views.add_hotel, name='add_hotel'),
    path('hotel/<int:hotel_id>/', views.hotel_detail, name='hotel_detail'),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('booking/confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('management/', views.management_view, name='management_view'),
    path('management/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('management/delete_hotel/<int:hotel_id>/', views.delete_hotel, name='delete_hotel'),
    path('management/edit_hotel/<int:hotel_id>/', views.edit_hotel, name='edit_hotel'),
    path('management/hotels/', views.hotel_management_view, name='hotel_management_view'),
    path('list_rooms/', views.list_rooms, name='list_rooms'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='booking/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='booking:hotel_list'), name='logout'),
    path('accounts/profile/', views.hotel_list, name='profile_redirect'),
    path('api/ai_chat/', views.ai_chat, name='ai_chat'),
]
