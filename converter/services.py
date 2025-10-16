import requests
from decimal import Decimal
from datetime import date
from django.conf import settings
from .models import ExchangeRate
from django.core.cache import cache
from .utils import seconds_until_end_of_day

FIXER_URL = "https://data.fixer.io/api/latest"

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504))
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))


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


def get_exchange_rate_usd_to(target_currency: str) -> Decimal:

    target_currency = target_currency.upper()
    today = date.today().isoformat() 
    cache_key = f"fx:USD:{target_currency}:{today}"

    cached = cache.get(cache_key)
    if cached:
        return Decimal(str(cached))

    try:
        er = ExchangeRate.objects.get(base='USD', target=target_currency, date=today)
        rate = er.rate
        ttl = seconds_until_end_of_day()
        cache.set(cache_key, str(rate), ttl)
        return rate
    except ExchangeRate.DoesNotExist:
        pass

    data = fetch_rates_from_fixer([target_currency, 'USD'])
    rates = data.get('rates', {})

    if target_currency not in rates or 'USD' not in rates:
        raise ValueError(f"Missing exchange rate for {target_currency} or USD in Fixer response: {rates.keys()}")


    eur_to_target = Decimal(str(rates.get(target_currency)))
    eur_to_usd = Decimal(str(rates.get('USD')))

    usd_to_target = (eur_to_target / eur_to_usd).quantize(Decimal('0.00000001'))

    ExchangeRate.objects.create(
        base='USD',
        target=target_currency,
        rate=usd_to_target,
        date=date.today(),
        source='fixer.io'
    )

    ttl = seconds_until_end_of_day()
    cache.set(cache_key, str(usd_to_target), ttl)

    return usd_to_target
