package org.gem.engine.hazard.memcached;

import java.util.Arrays;
import java.util.List;

import org.opensha.commons.data.Site;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;

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

    public void serialize(GEMHazardCurveRepository repository)
    {
        for (int i = 0; i < repository.getGridNode().size(); i++)
        {
            Site site = repository.getGridNode().get(i);

            // extracting needed values from the repository
            HazardCurveDTO hazardCurve = new HazardCurveDTO(site.getLocation().getLongitude(), site.getLocation()
                    .getLatitude(), repository.getGmLevels(), Arrays.asList(repository.getProbExceedanceList(i)));

            serialize(hazardCurve);
        }
    }

}
