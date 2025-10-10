from django.urls import path
from .views import CostsConvertedAPIView

urlpatterns = [
    path('costs/converted', CostsConvertedAPIView.as_view(), name='costs-converted'),
]
