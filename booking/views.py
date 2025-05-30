from django.shortcuts import render, get_object_or_404, redirect
from .models import Hotel, Room, Customer, Booking
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserActivity
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .forms import HotelForm, RoomForm, CustomerForm

def hotel_list(request):
    hotels = Hotel.objects.all()

    # Filtering parameters
    location = request.GET.get('location')
    min_rating = request.GET.get('min_rating')
    max_price = request.GET.get('max_price')
    amenities = request.GET.getlist('amenities')

    if request.user.is_authenticated and (location or min_rating or max_price):
        UserActivity.objects.create(
            user=request.user,
            location=location or '',
            min_rating=min_rating or 0,
            max_price=max_price or 0
        )

    if location:
        hotels = hotels.filter(location__icontains=location)
    if min_rating:
        hotels = hotels.filter(rating__gte=min_rating)
    if amenities:
        for amenity in amenities:
            hotels = hotels.filter(amenities__contains=amenity)

    if max_price:
        hotels = hotels.filter(rooms__price__lte=max_price).distinct()

    context = {
        'hotels': hotels,
        'filters': {
            'location': location or '',
            'min_rating': min_rating or '',
            'max_price': max_price or '',
            'amenities': amenities or [],
        }
    }
    return render(request, 'booking/hotel_list.html', context)

def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    rooms = hotel.rooms.filter(availability=True)
    return render(request, 'booking/hotel_detail.html', {'hotel': hotel, 'rooms': rooms})

@require_http_methods(["GET", "POST"])
@transaction.atomic
def book_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id, availability=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        if not all([name, email, phone, check_in, check_out]):
            return HttpResponse("All fields are required.", status=400)
        customer, created = Customer.objects.get_or_create(email=email, defaults={'name': name, 'phone': phone})
        booking = Booking.objects.create(
            customer=customer,
            room=room,
            check_in=check_in,
            check_out=check_out,
            status='confirmed'
        )
        room.availability = False
        room.save()
        return redirect(reverse('booking:booking_confirmation', args=[booking.id]))
    return render(request, 'booking/book_room.html', {'room': room})

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, 'booking/booking_confirmation.html', {'booking': booking})

@staff_member_required
def management_view(request):
    bookings = Booking.objects.select_related('customer', 'room', 'room__hotel').all()
    return render(request, 'booking/management_view.html', {'bookings': bookings})

@staff_member_required
@require_POST
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    booking.delete()
    return HttpResponseRedirect(reverse('booking:management_view'))

def list_rooms(request):
    rooms = Room.objects.all()
    return render(request, 'booking/list_rooms.html', {'rooms': rooms})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(customer__email=request.user.email).select_related('room', 'room__hotel')
    return render(request, 'booking/my_bookings.html', {'bookings': bookings})

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if name and email and message:
            send_mail(
                f'Contact Us Message from {name}',
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            return render(request, 'booking/contact_us.html', {'success': True})
        else:
            return render(request, 'booking/contact_us.html', {'error': 'All fields are required.'})
    return render(request, 'booking/contact_us.html')

def recommend_hotels(request):
    recommendations = [
        {
            "name": "Grand Plaza",
            "location": "New York",
            "price_range": "$120 - $180",
            "rating": 4.5,
            "amenities": ["wifi", "pool", "gym"]
        },
        {
            "name": "Sea View Resort",
            "location": "Miami",
            "price_range": "$200 - $250",
            "rating": 4.0,
            "amenities": ["wifi", "beach", "spa"]
        }
    ]
    return JsonResponse({"recommendations": recommendations})

@staff_member_required
def add_hotel(request):
    if request.method == "POST":
        form = HotelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hotel_list')
    else:
        form = HotelForm()
    return render(request, 'booking/add_hotel.html', {'form': form})

@staff_member_required
def add_room(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'booking/add_room.html', {'form': form})

@staff_member_required
def add_customer(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'booking/add_customer.html', {'form': form})
