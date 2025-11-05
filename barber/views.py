from django.shortcuts import render,redirect,get_object_or_404
from .forms import CustomUserCreationForm
from .models import UserProfile,Service,Booking
from django.http import JsonResponse,HttpResponse
import random
from django.conf import settings
import requests
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.forms import AuthenticationForm
import datetime
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.utils import timezone
import google.generativeai as genai
import json
from django.views.decorators.http import require_POST



# initilaize razorpya client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))



# Create your views here.
def home(request):
    services = Service.objects.all() 
    cart_service_ids=[]
    if request.user.is_authenticated:
        cart=request.session.get('cart',{})
        cart_service_ids=list(cart.keys())

    context={
        'services': services,
        'cart_service_ids': cart_service_ids

    }
    return render(request,'home.html',context)

# OTP bhjene  ke liye
def send_otp(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        # Phone number ko validate karo
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            return JsonResponse({'status': 'error', 'message': 'Please enter a valid 10-digit phone number.'})

        otp = random.randint(100000, 999999)
        
        request.session['signup_data'] = request.POST.dict()
        request.session['otp'] = otp

        # 2Factor API URL
        api_key = settings.TWOFACTOR_API_KEY
        url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}/RoyalBarberOTP"

        try:
            # API ko request bhejo
            response = requests.get(url)
            response_data = response.json()
            
            # Check karo ki SMS gaya ya nahi
            if response_data.get("Status") == "Success":
                print(f"OTP sent to {phone_number}")
                return JsonResponse({'status': 'success', 'message': 'OTP sent successfully!'})
            else:
                print(f"2Factor Error: {response_data.get('Details')}")
                return JsonResponse({'status': 'error', 'message': 'Failed to send OTP. Please try again.'})
        
        except Exception as e:
            print(f"Error connecting to 2Factor API: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# === VERIFY OTP FUNCTION  ===
def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')

        if str(stored_otp) == user_otp:
            signup_data = request.session.get('signup_data')
            form = CustomUserCreationForm(signup_data)
            
            if form.is_valid():
                user = form.save()
                UserProfile.objects.create(
                    user=user,
                    phone_number=form.cleaned_data.get('phone_number')
                )
                login(request, user)

                del request.session['signup_data']
                del request.session['otp']
                
                return JsonResponse({'status': 'success', 'message': 'Account created successfully!'})
            else:
                print("Form errors:", form.errors)

                errors = {field: error[0] for field, error in form.errors.items()}
                return JsonResponse({'status': 'error', 'message': 'Form is not valid.', 'errors': errors})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid OTP.'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required

def my_bookings(request):
    return render(request,'my_bookings.html')


# For adding services to cart
@login_required
def cart(request):
    # session se cart ka data nikalna
    cart_data=request.session.get('cart', {})

    # cart me jo services id h ,unhe ek list me dalo
    service_ids=cart_data.keys()

    # jo IDs niklai h unke hisab se services ko database se fetch karo
    services_in_cart=Service.objects.filter(id__in=service_ids)

    # Total price calculate krne ke liye
    total_price=0
    for service in services_in_cart:
        total_price+=service.price

    # for  adding date and time
    today=datetime.date.today()
    dates=[]
    for i in range(7):
        date=today +datetime.timedelta(days=i)
        dates.append({
            'date':date,
            'day_name':date.strftime('%a').upper(),
            'day_num':date.day,
            'month':date.strftime('%b').upper()

        })

    # For time
    time_slots=[]
    start_time=datetime.time(10,0)
    end_time=datetime.time(20,0)

    current_time=datetime.datetime.combine(today,start_time)
    end_datetime=datetime.datetime.combine(today,end_time)
    
    while current_time<=end_datetime:
        time_slots.append(current_time.strftime('%I:%M %p'))
        current_time+=datetime.timedelta(minutes=30)

    context={
        'cart_items':services_in_cart,
        'total_price':total_price,
        'dates':dates,
        'time_slots':time_slots,
        'rezorpay_key':settings.RAZORPAY_KEY_ID


    }

    return render(request,'cart.html',context)


def add_to_cart(request,service_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'login_required'})
    if request.method=="POST":
        # service ko database se dhondho
        service=get_object_or_404(Service,id=service_id)
        
        cart=request.session.get('cart',{})

        cart[str(service_id)]=1
        request.session['cart']=cart

        new_cart_count=len(cart)
        return JsonResponse({
            'status':'success',
            'message': 'Service added to cart!',
            'service_name': service.name,
            'new_cart_count': new_cart_count
        })
    return JsonResponse({'status':'error','message':'Invalid request'})

# For removing services from cart
@login_required
def remove_from_cart(request,service_id):
    if request.method=="POST":
        cart=request.session.get('cart',{})
        service_id_str=str(service_id)

        if service_id_str in cart:
            del cart[service_id_str]
            request.session['cart']=cart

            # new total ke liye
            remaining_ids=cart.keys()
            services_in_cart=Service.objects.filter(id__in=remaining_ids)
            new_total_price=sum(s.price for s in services_in_cart )

            new_cart_count=len(cart)

            return JsonResponse({'status': 'success', 'message': 'Service removed!', 'new_total': f'{new_total_price:.2f}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Service not in cart.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


# My bookings page dikhane ke liye
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user, status='Confirmed').order_by('-created_at')
    bookings_past = Booking.objects.filter(user=request.user, status__in=['Completed','Cancelled']).order_by('-created_at')

    return render(request, 'my_bookings.html', {'bookings': bookings ,'bookings_past':bookings_past})
# === VIEW FOR CANCEL BOOKING ===
@login_required
def cancel_booking(request,booking_id):
    booking=get_object_or_404(Booking,id=booking_id,user=request.user)
    try:
        if booking.status=='Confirmed':
            payment_id=booking.razorpay_payment_id
            amount=int(booking.total_amount*100)

            razorpay_client.payment.refund(payment_id,{'amount': amount})
            booking.status='Cancelled'
            booking.save()
            messages.success(request,f'Booking #{booking.id} cancelled and refund initiated.')  
        else:
            messages.error(request,'Only Confirmed bookings can be cancelled.')
    except Exception as e:
        messages.error(request,f'Error cancelling booking: {e}')
    return redirect('my_bookings')



# === VIEW #2: PAYMENT SHURU KARNE KE LIYE (RAZORPAY ORDER) ===
@login_required
def start_payment(request):
    if request.method == "POST":
        # Cart se total amount calculate karo
        cart_data = request.session.get('cart', {})
        service_ids = cart_data.keys()
        services = Service.objects.filter(id__in=service_ids)
        total_price = sum(s.price for s in services)
        amount_in_paise = int(total_price * 100) # Razorpay paise mein amount leta hai

        # Razorpay order create karo
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"receipt_user_{request.user.id}_{datetime.datetime.now().timestamp()}"
        }
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        # Ek nayi booking database mein banao (status='Pending')
        booking = Booking.objects.create(
            user=request.user,
            date=request.POST.get('date'),
            time_slot=request.POST.get('time_slot'),
            total_amount=total_price,
            rezorpay_order_id=razorpay_order['id']
        )
        booking.services.set(services)

        # Frontend ko zaroori details bhejo
        return JsonResponse({
            'status': 'success',
            'order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID,
            'name': 'Royal Barber',
            'user_name': request.user.username,
            'user_email': request.user.email,
            'user_phone': request.user.userprofile.phone_number if hasattr(request.user, 'userprofile') else ''
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# === VIEW #3: PAYMENT SUCCESSFUL HONE PAR HANDLE KARNE KE LIYE ===
@csrf_exempt
@login_required
def handle_payment_success(request):
    if request.method == "POST":
        try:
            # Razorpay se aayi details ko verify karo
            payment_data = {
                'razorpay_order_id': request.POST.get('razorpay_order_id'),
                'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
                'razorpay_signature': request.POST.get('razorpay_signature')
            }
            razorpay_client.utility.verify_payment_signature(payment_data)

            # Booking ko 'Confirmed' mark karo
            booking = Booking.objects.get(rezorpay_order_id=payment_data['razorpay_order_id'])
            booking.razorpay_payment_id = payment_data['razorpay_payment_id']
            booking.razorpay_signature = payment_data['razorpay_signature']
            booking.status = 'Confirmed'
            booking.save()
            
            # Cart ko khaali kar do
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True

            return JsonResponse({'status': 'success', 'message': 'Payment successful!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# Login ke liye
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'status': 'success', 'message': f'Welcome back, {username}!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid username or password.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# ----Log Out ek liye
def logout_view(request):
    logout(request)
    return redirect('home')



# === PASSWORD RESET VIEWS ===
def password_reset_phone(request):
    return render(request,'password_reset_phone.html')

def password_reset_send_otp(request):
    if request.method == "POST":
        phone_number=request.POST.get('phone_number')
        if not phone_number or not phone_number.isdigit() or len(phone_number)!=10:
            messages.error(request,"Please enter a valid Phone Number.")
            return redirect('password_reset_phone')
        
        try:
            user_profile=UserProfile.objects.get(phone_number=phone_number)
            user=user_profile.user

            otp=random.randint(100000,999999)

            request.session['reset_otp']=otp
            request.session['reset_user_id']=user.id
            request.session.set_expiry(300)

            # 2Factor API URL
            api_key=settings.TWOFACTOR_API_KEY
            url=f"https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}/RoyalBarberPasswordReset"

            try:
                response=requests.get(url)
                response_data=response.json()
                
                if response_data.get('Status')=='Success':
                    messages.success(request,f'OTP sent to {phone_number}. It is valid for 5 Minutes')
                    return redirect('password_reset_verify')
                else:
                    messages.error(request,f'Failed to send OTP. {response_data.get("Details","Unknown Error")}')

            except Exception as e:
                messages.error(request,f'Error connecting to OTP services: {e}')

        # End send OTP

        except UserProfile.DoesNotExist:
            messages.error(request,'No user found with this phone number.')
        except Exception as e:
            messages.error(request,f'An error occurred: {e}')
        
        return redirect('password_reset_phone')
    return redirect('password_reset_phone')
        

def password_reset_verify(request):
    if request.method=="GET":
        return render(request,'password_reset_verify.html')
    elif request.method=="POST":
        user_otp=request.POST.get('otp')
        new_password=request.POST.get('new_password')
        newpassword2=request.POST.get('new_password2')
        
        stored_otp=request.session.get('reset_otp')
        user_id=request.session.get('reset_user_id')

        if not user_otp or  not new_password or not newpassword2:
            messages.error(request,'Please fill all the fields.')
            return render(request,'password_reset_verify.html')
        
        if not stored_otp or not user_id:
            messages.error(request,'OTP has expired. Please start the process again.')
            return redirect('password_reset_phone')


        if str(stored_otp)!=user_otp:
            messages.error(request,'Invalid OTP.')
            return render(request,'password_reset_verify.html')
        
        if new_password!=newpassword2:
            messages.error(request,'Passwords do not match.')
            return render(request,'password_reset_verify.html')
        
        try:
            user=User.objects.get(id=user_id)

            user.set_password(new_password)
            user.save()

            if 'reset_otp' in request.session:
                del request.session['reset_otp']
            if 'reset_user_id' in request.session:
                del request.session['reset_user_id']

            messages.success(request,'Password reset successfully')
            return redirect('password_reset_completed')
        except User.DoesNotExist:
            messages.error(request,'User not found. Please start the process again.')
            return redirect('password_reset_phone')
        except Exception as e:
            messages.error(request,f'An error occurred: {e}')
            return render(request,'password_reset_verify.html')
        

# === DASHBOARD VIEW FOR ADMIN/STAFF ===
@user_passes_test(lambda u: u.is_staff)
def dashboard_view(request):
    today=timezone.now().date()

    # get all bookings
    today_bookings=Booking.objects.filter(date=today,status='Confirmed')
    upcoming_bookings=Booking.objects.filter(date__gt=today,status='Confirmed')
    previous_bookings=Booking.objects.filter(status__in=['Cancelled','Completed'])
    context={
        'today_bookings':today_bookings,
        'upcoming_bookings':upcoming_bookings,
        'previous_bookings':previous_bookings,
    }

    return render(request,'dashboard.html',context)

@user_passes_test(lambda u: u.is_staff)
def dashboard_complete_booking(request,booking_id):
    booking=get_object_or_404(Booking,id=booking_id)
    booking.status='Completed'
    booking.save()
    messages.success(request,f'Booking #{booking.id} marked as Completed')
    return redirect('dashboard')

@user_passes_test(lambda u: u.is_staff)
def dashboard_cancel_booking(request,booking_id):
    booking=get_object_or_404(Booking,id=booking_id)
    try:
        if booking.status=='Confirmed':
            payment_id=booking.razorpay_payment_id
            amount=int(booking.total_amount*100)

            razorpay_client.payment.refund(payment_id,{'amount': amount})
            booking.status="Cancelled"
            booking.save()
            messages.success(request,f'Booking #{booking.id} cancelled and refund initiated.')
        else:
            messages.error(request,'Only Confirmed bookings can be cancelled.')
    except Exception as e:
        messages.error(request,f'Error cancelling booking: {e}')    
    return redirect('dashboard')


@require_POST
def  ask_ai_view(request):
    if not settings.GEMINI_API_KEY:
        return JsonResponse({'status':'error','message':'AI Assistant is not configured.'})
    

    # User ka sawal nikalo
    try:
        data=json.loads(request.body)
        question=data.get('question')

        if not question:
            return JsonResponse({'error': 'No question provided.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    

    # AI ko setup karo
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # 4. Persona (AI ka role) define karo - YEH SABSE ZAROORI HAI
        system_prompt = (
            "You are 'Royal Barber Assistant', a helpful AI for a barber shop. "
            "Your tone is friendly and professional. "
            "Your knowledge is strictly limited to this barber shop. "
            "Our services include: Haircut & Styling (Rs. 199), Beard Trim & Styling (Rs. 199), Shaving (Rs. 150), Facial (Rs. 499). "
            "Our hours are 10:00 AM to 8:00 PM, Tuesday to Sunday (Monday closed). "
            "Do not answer any questions unrelated to the barber shop (like history, science, math, coding, etc.). "
            "If asked an unrelated question, politely decline by saying: 'I can only help with questions about Royal Barber services and bookings.'"
        )

        response=model.generate_content(system_prompt + "\n\nUser Question: " +question)

        return JsonResponse({'answer': response.text})
    except Exception as e:
        print(f"!!!  AI ERROR: {e}")
        return JsonResponse({'error': 'The AI service is currently unavailable. Please try again later.'}, status=500)    
