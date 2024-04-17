from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from .models import *
import razorpay
from base.helper import *
from datetime import datetime


# Create your views here.
def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user_obj = User.objects.filter(username=email)
        if not user_obj.exists():
            messages.warning(request, "User not registered")
            return HttpResponseRedirect(request.path_info)

        if not user_obj[0].profile.is_email_verified:
            messages.warning(request, "Account not verified")
            return HttpResponseRedirect(request.path_info)

        user_obj = authenticate(username=email, password=password)
        if user_obj:
            login(request, user_obj)
            return redirect("/")
        messages.warning(request, "Invalid email/password")
        return HttpResponseRedirect(request.path_info)

    return render(request, "accounts/login.html")


def register_page(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user_obj = User.objects.filter(username=email)
        if user_obj.exists():
            messages.warning(request, "User already registered")
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create(
            first_name=first_name, last_name=last_name, email=email, username=email
        )
        user_obj.set_password(password)
        user_obj.save()
        messages.success(request, "An email has been sent on your mail")
        return HttpResponseRedirect(request.path_info)
    return render(request, "accounts/register.html")


def activate_email(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verified = True
        user.save()
        return redirect("/")
    except Exception as e:
        return HttpResponse("Invalid Email token")


def add_to_cart(request, uid):
    print(uid)
    print("+++++++++++++++++=")
    variant = request.GET.get("variant")
    product = Product.objects.get(uid=uid)
    user = request.user

    cart, _ = Cart.objects.get_or_create(user=user, is_paid=False)
    cart_item = CartItem.objects.create(cart=cart, product=product)

    if variant:
        variant = request.GET.get("variant")
        size_variant = SizeVariant.objects.get(size_name=variant)
        cart_item.size_variant = size_variant
        cart_item.save()

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def remove_cart(request, cart_item_uid):
    try:
        cart_item = CartItem.objects.get(uid=cart_item_uid)
        cart_item.delete()
    except Exception as e:
        print(e)

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


from django.conf import settings


def cart(request):
    cart_obj = None
    info = {}
    try:
        cart_obj = Cart.objects.get(is_paid=False, user=request.user)
    except Exception as e:
        print(e)
    if request.method == "POST":
        coupon = request.POST.get("coupon")
        coupon_obj = Coupon.objects.filter(coupon_code=coupon)
        if not coupon_obj.exists():
            messages.warning(request, "Invalid Coupon")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))
        if cart_obj.coupon:
            messages.warning(request, "Coupon already applied")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        if cart_obj.get_cart_total() < coupon_obj[0].min_amount:
            messages.warning(
                request, f"Amount should be greater than {coupon_obj[0].min_amount}"
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        if coupon_obj[0].is_expired:
            messages.warning(request, "Coupon is expired")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

        cart_obj.coupon = coupon_obj[0]
        cart_obj.save()
        messages.success(request, "Coupon applied")
    payment = None
    if cart_obj:
        client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
        payment = client.order.create(
            {
                "amount": cart_obj.get_cart_total() * 100,
                "currency": "INR",
                "payment_capture": 1,
            }
        )
        cart_obj.razor_pay_order_id = payment["id"]
        cart_obj.save()
        info["order_id"] = payment["id"]
        info["date"] = datetime.now()
        info["product"] = cart_obj
        info["user_name"] = request.user.first_name + " " + request.user.last_name
        info["email"] = request.user.email
        save_pdf(info)
    context = {"cart": cart_obj, "payment": payment}
    return render(request, "accounts/cart.html", context)


def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid=cart_id)
    cart.coupon = None
    cart.save()
    messages.warning(request, "Coupon removed")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def success(request):
    order_id = request.GET.get("order_id")
    cart = Cart.objects.get(razor_pay_order_id=order_id)
    cart.is_paid = True
    cart.save()
    return HttpResponse("Payment succes")
