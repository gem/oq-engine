package org.gem.calc;

public class UHSResult
{
    private double poe;
    private Double[] uhs;

    public UHSResult(double poe, Double[] uhs)
    {
        this.poe = poe;
        this.uhs = uhs;
    }

    public double getPoe()
    {
        return poe;
    }

    public Double[] getUhs()
    {
        return uhs;
    }
}
