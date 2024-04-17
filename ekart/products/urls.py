from django.urls import path, include
from .views import *

urlpatterns = [
    path("<slug>/", get_products, name="get_products"),
]
