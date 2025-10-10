import requests
from decimal import Decimal
from datetime import date
from django.conf import settings
from .models import ExchangeRate

FIXER_URL = "https://data.fixer.io/api/latest"

def fetch_rates_from_fixer(symbols):
    params = {
        'access_key': settings.FIXER_API_KEY,
        'symbols': ','.join(symbols)
    }
    r = requests.get(FIXER_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_exchange_rate_usd_to(target_currency: str) -> Decimal:
    today = date.today()
    target_currency = target_currency.upper()

    try:
        er = ExchangeRate.objects.get(base='USD', target=target_currency, date=today)
        return er.rate

    except ExchangeRate.DoesNotExist:
        data = fetch_rates_from_fixer([target_currency, 'USD'])

        rates = data.get('rates', {})
        eur_to_target = Decimal(str(rates.get(target_currency)))
        eur_to_usd = Decimal(str(rates.get('USD')))
        usd_to_target = (eur_to_target / eur_to_usd).quantize(Decimal('0.00000001'))

        ExchangeRate.objects.create(
            base='USD',
            target=target_currency,
            rate=usd_to_target,
            date=today,
            source='fixer.io'
        )

        return usd_to_target
