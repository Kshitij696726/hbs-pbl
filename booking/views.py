import spacy
from django.shortcuts import render, get_object_or_404, redirect
from .models import Hotel, Room, Customer, Booking
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.db.models import Q, Avg
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import HotelRatingForm, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import HotelRating
from .utils import get_hotel_embedding, compute_embedding, compute_similarity
import numpy as np

def hotel_list(request):
    hotels = Hotel.objects.annotate(avg_rating=Avg('ratings__rating'))

    # Filtering parameters
    location = request.GET.get('location')
    min_rating = request.GET.get('min_rating')
    max_price = request.GET.get('max_price')
    amenities = request.GET.getlist('amenities')
    keyword = request.GET.get('keyword', '').strip()

    if location:
        hotels = hotels.filter(location__icontains=location)
    if min_rating:
        hotels = hotels.filter(avg_rating__gte=min_rating)
    if amenities:
        # Score hotels by number of matching amenities
        hotel_list = list(hotels)
        scored = []
        for hotel in hotel_list:
            match_count = sum(amenity.lower() in [a.lower() for a in hotel.amenities] for amenity in amenities if hotel.amenities)
            if match_count > 0:
                scored.append((match_count, hotel))
        scored.sort(reverse=True, key=lambda x: x[0])
        hotels = [h[1] for h in scored]

    if keyword:
        # Compute embedding for keyword
        keyword_embedding = compute_embedding(keyword)

        # Filter hotels by semantic similarity
        hotel_list = list(hotels)
        hotel_embeddings = [get_hotel_embedding(h) for h in hotel_list]

        similarities = [compute_similarity(keyword_embedding, emb) for emb in hotel_embeddings]

        # Debug print similarity scores
        print("Similarity scores for hotels:")
        for hotel, sim in zip(hotel_list, similarities):
            print(f"{hotel.name}: {sim}")

        # Threshold for similarity filtering
        threshold = 0.3
        filtered_hotels = [hotel for hotel, sim in zip(hotel_list, similarities) if sim >= threshold]

        # Keyword substring matching (case-insensitive)
        keyword_lower = keyword.lower()
        keyword_matched_hotels = [hotel for hotel in hotel_list if
                                  (hotel.description and keyword_lower in hotel.description.lower()) or
                                  (hotel.amenities and any(keyword_lower in amenity.lower() for amenity in hotel.amenities))]

        # Combine both sets (union)
        combined_hotels = list({*filtered_hotels, *keyword_matched_hotels})

        # Sort combined hotels by similarity descending (hotels without similarity get 0)
        combined_hotels.sort(key=lambda h: similarities[hotel_list.index(h)] if h in filtered_hotels else 0, reverse=True)

        hotels = combined_hotels

    # Sort hotels by creation date descending to show newly added hotels first
    hotels = sorted(hotels, key=lambda h: h.id, reverse=True)

    context = {
        'hotels': hotels,
        'filters': {
            'location': location or '',
            'min_rating': min_rating or '',
            'max_price': max_price or '',
            'amenities': amenities or [],
            'keyword': keyword,
        }
    }
    return render(request, 'booking/hotel_list.html', context)

def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    rooms = hotel.rooms.filter(availability=True)
    user_rating = None
    if request.user.is_authenticated:
        try:
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            customer = Customer.objects.create(user=request.user, name=request.user.username, email=request.user.email, phone='')
        if request.method == 'POST':
            form = HotelRatingForm(request.POST)
            if form.is_valid():
                rating_value = form.cleaned_data['rating']
                rating_obj, created = HotelRating.objects.update_or_create(
                    hotel=hotel,
                    customer=customer,
                    defaults={'rating': rating_value}
                )
        else:
            form = HotelRatingForm()
        try:
            user_rating = HotelRating.objects.get(hotel=hotel, customer=customer).rating
        except HotelRating.DoesNotExist:
            user_rating = None
    else:
        form = None

    avg_rating = hotel.ratings.aggregate(Avg('rating'))['rating__avg'] or 0.0
    hotel.rating = avg_rating
    hotel.save(update_fields=['rating'])

    context = {
        'hotel': hotel,
        'rooms': rooms,
        'form': form,
        'user_rating': user_rating,
        'avg_rating': avg_rating,
    }
    return render(request, 'booking/hotel_detail.html', context)

@require_http_methods(["GET", "POST"])
@transaction.atomic
@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id, availability=True)
    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        if not all([check_in, check_out]):
            return HttpResponse("Check-in and check-out dates are required.", status=400)
        try:
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            customer = Customer.objects.create(user=request.user, name=request.user.username, email=request.user.email, phone='')
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

from .forms import HotelForm
from django.contrib import messages

from .forms import HotelForm
from django.contrib import messages

from django.views.decorators.http import require_http_methods
from django.contrib import messages

@staff_member_required
def management_view(request):
    bookings = Booking.objects.select_related('customer', 'room', 'room__hotel').all()
    context = {
        'bookings': bookings,
    }
    return render(request, 'booking/management_view.html', context)

@staff_member_required
def hotel_management_view(request):
    hotels = Hotel.objects.all()

    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES)
        if form.is_valid():
            hotel = form.save()
            room_type = form.cleaned_data['room_type']
            price = form.cleaned_data['price']
            Room.objects.create(
                hotel=hotel,
                room_type=room_type,
                price=price,
                availability=True
            )
            messages.success(request, f'Hotel "{hotel.name}" and room added successfully.')
            return redirect('booking:hotel_management_view')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HotelForm()

    context = {
        'hotels': hotels,
        'form': form,
    }
    return render(request, 'booking/hotel_management_view.html', context)

@staff_member_required
def edit_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    try:
        room = hotel.rooms.first()
    except:
        room = None

    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES, instance=hotel)
        if form.is_valid():
            hotel = form.save()
            room_type = form.cleaned_data['room_type']
            price = form.cleaned_data['price']
            if room:
                room.room_type = room_type
                room.price = price
                room.save()
            else:
                Room.objects.create(
                    hotel=hotel,
                    room_type=room_type,
                    price=price,
                    availability=True
                )
            messages.success(request, f'Hotel "{hotel.name}" updated successfully.')
            return redirect('booking:management_view')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        if room:
            initial['room_type'] = room.room_type
            initial['price'] = room.price
        form = HotelForm(instance=hotel, initial=initial)

    context = {
        'form': form,
        'hotel': hotel,
    }
    return render(request, 'booking/edit_hotel.html', context)

from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect

from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse

@staff_member_required
@require_POST
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    booking.delete()
    return HttpResponseRedirect(reverse('booking:management_view'))

@staff_member_required
@require_POST
def delete_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    hotel.delete()
    return HttpResponseRedirect(reverse('booking:management_view'))

def list_rooms(request):
    rooms = Room.objects.all()
    return render(request, 'booking/list_rooms.html', {'rooms': rooms})

@login_required
def my_bookings(request):
    try:
        customer = request.user.customer_profile
    except Customer.DoesNotExist:
        customer = Customer.objects.create(user=request.user, name=request.user.username, email=request.user.email, phone='')

    if request.method == 'POST':
        hotel_id = request.POST.get('hotel_id')
        rating_value = request.POST.get('rating')
        if hotel_id and rating_value:
            try:
                hotel = Hotel.objects.get(id=hotel_id)
                rating_value_int = int(rating_value)
                if 1 <= rating_value_int <= 5:
                    HotelRating.objects.update_or_create(
                        hotel=hotel,
                        customer=customer,
                        defaults={'rating': rating_value_int}
                    )
            except Hotel.DoesNotExist:
                pass

    bookings = Booking.objects.filter(customer=customer).select_related('room', 'room__hotel')

    rating_forms = {}
    user_ratings = []
    for booking in bookings:
        hotel = booking.room.hotel
        try:
            user_rating_obj = HotelRating.objects.get(hotel=hotel, customer=customer)
            user_ratings.append({'hotel_id': hotel.id, 'rating': user_rating_obj.rating})
        except HotelRating.DoesNotExist:
            user_ratings.append({'hotel_id': hotel.id, 'rating': None})
        rating_forms[hotel.id] = HotelRatingForm()

    context = {
        'bookings': bookings,
        'rating_forms': rating_forms,
        'user_ratings': user_ratings,
    }
    return render(request, 'booking/my_bookings.html', context)

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

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Check if Customer profile already exists for this user
            if not hasattr(user, 'customer_profile'):
                Customer.objects.create(user=user, name=user.username, email=user.email, phone='')
            return redirect('booking:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'booking/register.html', {'form': form})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import google.generativeai as genai
import json
from django.contrib.auth.decorators import login_required

@csrf_exempt
@login_required
def ai_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            if not user_message:
                return JsonResponse({'error': 'Empty message'}, status=400)

            api_key = settings.GEMINI_API_KEY
            if not api_key:
                return JsonResponse({'error': 'Gemini API key not configured'}, status=500)

            client = genai.Client(api_key=api_key)

            system_prompt = (
                "You are an AI assistant for a hotel booking website. "
                "The website allows users to browse hotels, view hotel details including rooms and amenities, "
                "make room bookings with check-in and check-out dates, and manage their bookings. "
                "Users can register, login, and view their booking history. "
                "Admins can manage hotels, rooms, and bookings through a management interface. "
                "The website supports hotel ratings and user reviews. "
                "Answer questions only based on these features and information. "
                "Do not provide information outside the scope of the website."
            )

            contents = [
                system_prompt,
                user_message
            ]

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents
            )

            answer = response.text if hasattr(response, 'text') else str(response)

            return JsonResponse({'answer': answer})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

from django.shortcuts import render

def add_hotel(request):
    # You can modify this based on your form logic
    return render(request, 'booking/add_hotel.html')
