# booking/forms.py
from django import forms
from booking.models import Hotel, Room, Customer

class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = '__all__'

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
