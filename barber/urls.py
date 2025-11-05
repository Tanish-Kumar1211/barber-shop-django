from django.contrib import admin
from django.urls import path,include
from .import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('',views.home,name='home'),

    path('send-otp/',views.send_otp,name='send_otp'),
    path('verify-otp/',views.verify_otp,name='verify_otp'),


    path('cart/',views.cart,name='cart'),

    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),

    path('add_to_cart/<int:service_id>/',views.add_to_cart,name="add_to_cart"),
    path('remove_from_cart/<int:service_id>/',views.remove_from_cart,name='remove_from_cart'),

    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('payment/start/', views.start_payment, name='start_payment'),
    path('payment/success/', views.handle_payment_success, name='handle_payment_success'),

    path('cancel_booking/<int:booking_id>/',views.cancel_booking,name='cancel_booking'),

    path('password-reset/phone/',views.password_reset_phone,name='password_reset_phone'),
    path('password-reset/send-otp/',views.password_reset_send_otp,name='password_reset_send_otp'),
    path('password-reset/verify/',views.password_reset_verify,name='password_reset_verify'),
    path('password-reset/completed/',TemplateView.as_view(template_name='password_reset_completed.html'),name='password_reset_completed'),

    path('dashboard/',views.dashboard_view,name='dashboard'),
    path('dashboard/booking/complete/<int:booking_id>/',views.dashboard_complete_booking,name='dashboard_complete_booking'),
    path('dashboard/booking/cancel/<int:booking_id>/',views.dashboard_cancel_booking,name='dashboard_cancel_booking'),

    path('ask-ai/',views.ask_ai_view,name='ask_ai'),
]
