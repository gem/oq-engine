package org.gem.engine.hazard.memcached;

import java.util.List;

public class HazardCurveSerializer
{

    private final String key;
    private final Cache cache;

    public HazardCurveSerializer(String key, Cache cache)
    {
        this.key = key;
        this.cache = cache;
    }

    public void serialize(HazardCurveDTO hazardCurve)
    {
        cache.set(key, hazardCurve.toJSON());
    }

    public void serialize(List<HazardCurveDTO> hazardCurves)
    {
        for (HazardCurveDTO hazardCurve : hazardCurves)
        {
            serialize(hazardCurve);
        }
    }

}
