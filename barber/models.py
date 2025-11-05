from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    phone_number=models.CharField(max_length=15)
    
    def __str__(self):
        return self.user.username


# Service model for storing services
class Service(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    duration = models.IntegerField()  # minutes mein
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    def __str__(self):
        return self.name
    
# Staff ki details store krega
class Staff(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    specialty=models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


# bookings ki detail yaha pr store hogi
class Booking(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    services=models.ManyToManyField(Service)
    date=models.DateField()
    time_slot=models.CharField(max_length=20,default='09:00 AM - 10:00 AM')
    total_amount=models.DecimalField(max_digits=10,decimal_places=2 ,default=0.00)
    # "Pending status add kiya gya hai payment ke liye"
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Pending')
    
    created_at=models.DateTimeField(auto_now_add=True)
    staff=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,blank=True)


    # Razorpay ki details save krne ke liye 
    rezorpay_order_id=models.CharField(max_length=100,null=True,blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f'booking for {self.user.username} on {self.date} at {self.time_slot}'

