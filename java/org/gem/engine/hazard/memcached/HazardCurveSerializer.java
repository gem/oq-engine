package org.gem.engine.hazard.memcached;

import java.util.Arrays;
import java.util.List;

import org.opensha.commons.data.Site;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;

/**
 * A simple JSON hazard curve serializer.
 * 
 * @author Andrea Cerisara
 */
public class HazardCurveSerializer
{

    private final String key;
    private final Cache cache;

    /**
     * Main constructor.
     * 
     * @param key the key used to store data in cache
     * @param cache the cache used
     */
    public HazardCurveSerializer(String key, Cache cache)
    {
        this.key = key;
        this.cache = cache;
    }

    /**
     * Serializes a single hazard curve.
     * 
     * @param hazardCurve the curve to serialize
     */
    public void serialize(HazardCurveDTO hazardCurve)
    {
        cache.set(key, hazardCurve.toJSON());
    }

    /**
     * Serializes the list of hazard curves.
     * 
     * @param hazardCurves the list of curves to serialize
     */
    public void serialize(List<HazardCurveDTO> hazardCurves)
    {
        for (HazardCurveDTO hazardCurve : hazardCurves)
        {
            serialize(hazardCurve);
        }
    }

    /**
     * Serializes all the curves stored in the repository
     * 
     * @param repository the repository used as source
     */
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
