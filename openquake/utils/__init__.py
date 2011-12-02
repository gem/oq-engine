"""This is needed for imports to work."""


import decimal

from openquake import java


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


def list_to_jdouble_array(float_list):
    """Convert a 1D list of floats to a 1D Java Double[] (as a jpype object).
    """
    jp = java.jvm()
    jdouble = jp.JArray(jp.java.lang.Double)(len(float_list))

    for i, val in enumerate(float_list):
        jdouble[i] = jp.JClass('java.lang.Double')(val)

    return jdouble
