from django.shortcuts import render

from decimal import Decimal, ROUND_HALF_UP
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import get_exchange_rate_usd_to
import requests
from django.conf import settings


class CostsConvertedAPIView(APIView):

    def get(self, request):
        target_currency = request.query_params.get('currency', 'PLN').upper()

        filters = {
            k: v for k, v in request.query_params.items()
            if k.lower() != 'currency'
        }

        try:
            response = requests.get(
                    settings.STAG_BASE_URL,
                    params={**filters, 'secret_key': settings.STAG_SECRET_KEY},
                    headers={'User-Agent': 'converter/1.0'},
                    timeout=10
                )
            response.raise_for_status()
            internal_data = response.json()
        except requests.RequestException as e:
            return Response(
                {'error': f'Błąd przy pobieraniu danych z API wewnętrznego: {e}'},
                status=status.HTTP_502_BAD_GATEWAY
            )   

        try:
            rate = get_exchange_rate_usd_to(target_currency)
        except Exception as e:
            return Response(
                {'error': f'Nie udało się pobrać kursu waluty: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        data = internal_data.get('data', [])
        for item in data:
            cost_usd = Decimal(str(item.get('cost_usd', 0)))
            converted = (cost_usd * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            item[f'cost_{target_currency.lower()}'] = float(converted)

        return Response({
            'currency': target_currency,
            'exchange_rate': float(rate),
            'data': data
        })
