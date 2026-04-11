"""Spell BDT totals in English (Taka / Paisa) for invoices."""
from decimal import Decimal, InvalidOperation

_ONES = (
    'Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen',
)
_TENS = (
    '', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety',
)


def _under_hundred(n: int) -> str:
    if n < 20:
        return _ONES[n]
    t, o = n // 10, n % 10
    if o:
        return f'{_TENS[t]} {_ONES[o]}'
    return _TENS[t]


def _under_thousand(n: int) -> str:
    if n < 100:
        return _under_hundred(n)
    h, r = n // 100, n % 100
    if r:
        return f'{_ONES[h]} Hundred {_under_hundred(r)}'
    return f'{_ONES[h]} Hundred'


def int_to_words(n: int) -> str:
    if n == 0:
        return 'Zero'
    if n < 0:
        return f'Negative {int_to_words(-n)}'
    parts = []
    for scale, name in ((1000000000, 'Billion'), (1000000, 'Million'), (1000, 'Thousand')):
        if n >= scale:
            parts.append(_under_thousand(n // scale))
            parts.append(name)
            n %= scale
    if n > 0:
        parts.append(_under_thousand(n))
    return ' '.join(parts)


def bdt_amount_in_words(amount) -> str:
    try:
        d = Decimal(str(amount)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return ''
    neg = d < 0
    d = abs(d)
    whole = int(d)
    paisa = int((d * 100) % 100)
    core = int_to_words(whole)
    if neg:
        core = f'Negative {core}'
    if paisa:
        return f'{core} Taka and {int_to_words(paisa)} Paisa only'
    return f'{core} Taka only'
