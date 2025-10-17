from decimal import Decimal, ROUND_HALF_UP
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from .services import get_exchange_rate_usd_to

class CostsConvertedAPIView(APIView):
    def get(self, request):
        target_currency_list = request.query_params.getlist('currency')
        target_currency = (target_currency_list[0] if target_currency_list else 'PLN').upper()
        filters = {k: v for k, v in request.query_params.items() if k.lower() != 'currency'}

        internal_data = {"data": []}
        data = []
        try:
            resp = requests.get(
                settings.STAG_BASE_URL,
                params={**filters, 'secret_key': settings.STAG_SECRET_KEY},
                headers={'User-Agent': 'converter/1.0'},
                timeout=10
            )
            resp.raise_for_status()
            internal_data = resp.json()
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)



        try:
            rate = get_exchange_rate_usd_to(target_currency)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        target_field = f"cost_{target_currency.lower()}"
        for item in data:
            cost_usd = Decimal(str(item.get('cost_usd', 0)))
            converted = (cost_usd * Decimal(str(rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            item[target_field] = float(converted)

        return Response({
            "currency": target_currency,
            "exchange_rate": float(rate),
            "data": data
        })
