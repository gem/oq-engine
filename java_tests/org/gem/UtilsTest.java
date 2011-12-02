package org.gem;

import static org.gem.Utils.digitize;
import static org.junit.Assert.*;

import org.junit.Test;

public class UtilsTest
{
    public static final Double[] BIN_LIMS = {5.0, 6.0, 7.0, 8.0, 9.0};

    @Test
    public void testDigitize()
    {
        int expected = 3;

        int actual = digitize(BIN_LIMS, 8.9);

        assertEquals(expected, actual);
    }

    @Test(expected=IllegalArgumentException.class)
    public void testDigitizeOutOfRange()
    {
        digitize(BIN_LIMS, 4.9);
    }

}
