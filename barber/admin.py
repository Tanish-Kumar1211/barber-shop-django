from django.contrib import admin
from .models import  Service,UserProfile,Booking,Staff
# Register your models here.


admin.site.register(UserProfile)
admin.site.register(Service)
admin.site.register(Booking)
admin.site.register(Staff)