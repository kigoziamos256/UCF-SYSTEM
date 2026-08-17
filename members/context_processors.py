from .models import Currency

def currency_context(request):
    try:
        default_currency = Currency.objects.get(is_default=True)
    except Currency.DoesNotExist:
        default_currency = Currency.objects.first()
    if not default_currency:
        default_currency, _ = Currency.objects.get_or_create(
            code='UGX',
            defaults={'symbol': 'UGX', 'name': 'Uganda Shilling', 'is_default': True}
        )
    return {
        'currency_symbol': default_currency.symbol,
        'currency_code': default_currency.code,
    }
