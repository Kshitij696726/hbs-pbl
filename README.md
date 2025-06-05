
# 🏨 Hotel Booking Management System

A web-based Hotel Booking Management System built with **Django**, enabling users to browse and book hotel rooms and allowing admins to manage bookings, customers, and room availability with ease.

## 🚀 Features

### 🧑‍💼 Admin Panel
- Dashboard with analytics
- Manage Rooms (Add/Edit/Delete)
- Manage Bookings
- Manage Customers
- Manage Room Categories
- Booking status updates (Pending, Confirmed, Cancelled)

### 🙋‍♂️ User Panel
- Register / Login / Logout
- Search available rooms by date & category
- Book rooms and manage personal bookings
- View booking history
- Receive booking confirmation

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML5, CSS3, Bootstrap, JavaScript
- **Database**: SQLite (default) or MySQL/PostgreSQL
- **Authentication**: Django's built-in auth system

## 📁 Basic Project Structure
``` 
hotel_booking_system/
│
├── bookings/ # Main app: bookings, rooms, customers
├── users/ # Custom user model and authentication
├── templates/ # HTML templates
├── static/ # Static files (CSS, JS, images)
├── hotel_booking_system/ # Django project settings and configurations
├── manage.py # Django management script
└── requirements.txt # Python dependencies
```

## ✅ Installation

### Prerequisites

- Python 3.8+
- pip
- virtualenv (optional but recommended)

### Steps
[bash]
# Clone the repository
git clone https://github.com/yourusername/hotel-booking-system.git
cd hotel-booking-system

# Create virtual environment
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser

# Run the development server
python manage.py runserver
Now open your browser and visit: http://127.0.0.1:8000/

# Admin Access:

Admin Panel: http://127.0.0.1:8000/admin/

Use the credentials created during createsuperuser

# Dependencies

List is in requirements.txt. Some key packages:

Django

Pillow (for image uploads)

crispy-forms (optional for better form UI)

--python manage.py createsuperuser (used to create admin , you will need this run to get management view)

# Optional Enhancements
Email notifications on booking

Payment gateway integration (Razorpay, Stripe)

Calendar view for admin bookings

API support with Django REST Framework

# License
This project is licensed under the MIT License.

# Contribution
Contributions are welcome! Feel free to fork this repo, make changes, and create pull requests.
