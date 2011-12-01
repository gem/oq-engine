package org.gem;

public class Utils
{
    /**
     * Given a list of 'bins' and a value,
     * figure out which bin the value fits into.
     * 
     * Examples:
     * 
     * Given the bins [0.0, 1.0, 2.0],
     * a value of 0.5 would be in bin 0, since it is
     * >= the 0th element and less then and 1st element.
     * 
     * Given the bins [0.0, 1.0, 2.0],
     * a value of 1.0 would be in bin 1.
     * @param bins
     * @param value
     */
    public static int digitize(Double[] bins, Double value)
    {
        for (int i = 0; i < bins.length - 1; i++)
        {
            if (value >= bins[i] && value < bins[i + 1])
            {
                return i;
            }
        }
        throw new IllegalArgumentException(
                "Value '" + value + "' is outside the expected range");
    }
}
