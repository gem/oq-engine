package org.gem.engine.hazard.memcached;

import java.io.Serializable;

public class AReallyCoolObject implements Serializable
{

    private static final long serialVersionUID = -4185818094252288027L;

    private final Double x;
    private final Double y;

    public AReallyCoolObject(Double x, Double y)
    {
        this.x = x;
        this.y = y;
    }

    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof AReallyCoolObject))
        {
            return false;
        }

        AReallyCoolObject other = (AReallyCoolObject) obj;
        return other.x.equals(x) && other.y.equals(y);
    }

}
