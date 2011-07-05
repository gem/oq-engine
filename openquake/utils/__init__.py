"""This is needed for imports to work."""


import decimal


def round_float(value):
    """
    Takes a float and rounds it to a fixed number of decimal places.

    This function makes uses of the built-in
    :py:method:`decimal.Decimal.quantize` to limit the precision.

    The 'round-half-even' algorithm is used for rounding.

    This should give us what can be considered 'safe' float values for
    geographical coordinates (to side-step precision and rounding errors).

    :type value: float

    :returns: the input value rounded to a hard-coded fixed number of decimal
    places
    """
    float_decimal_places = 7
    quantize_str = '0.' + '0' * float_decimal_places

    return float(
        decimal.Decimal(str(value)).quantize(
            decimal.Decimal(quantize_str),
            rounding=decimal.ROUND_HALF_EVEN))
