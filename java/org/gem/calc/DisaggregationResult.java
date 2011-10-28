package org.gem.calc;

public class DisaggregationResult
{
    private double[][][][][] matrix;
    private double gmv;

    public double[][][][][] getMatrix()
    {
        return matrix;
    }

    public void setMatrix(double[][][][][] matrix)
    {
        this.matrix = matrix;
    }

    public double getGMV()
    {
        return gmv;
    }

    public void setGMV(double gmv)
    {
        this.gmv = gmv;
    }
}
