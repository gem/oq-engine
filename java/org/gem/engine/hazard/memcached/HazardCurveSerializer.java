package org.gem.engine.hazard.memcached;

import java.util.Arrays;

import org.opensha.commons.data.Site;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepositoryList;

import com.google.gson.Gson;

/**
 * A simple JSON hazard curve serializer.
 * 
 * @author Andrea Cerisara
 */
public class HazardCurveSerializer
{

    private final Cache cache;

    /**
     * Main constructor.
     * 
     * @param cache the cache used to store data
     */
    public HazardCurveSerializer(Cache cache)
    {
        this.cache = cache;
    }

    /**
     * Serializes a single hazard curve.
     * 
     * @param hazardCurve the curve to serialize
     */
    private void serialize(HazardCurveDTO hazardCurve)
    {
        cache.set(generateKey(hazardCurve), hazardCurve.toJSON());
    }

    private String generateKey(HazardCurveDTO hazardCurve)
    {
        return new StringBuilder(hazardCurve.getLongitude().toString()).append(
                "+").append(hazardCurve.getLatitude()).toString();
    }

    /**
     * Serializes all the curves stored in the repository
     * 
     * @param repository the repository used as source
     */
    public void serialize(GEMHazardCurveRepositoryList repository)
    {
        System.out.println(new Gson().toJson(repository));
        
        for (int i = 0; i < repository.getHcRepList().size(); i++)
        {
            String endBranchLabel = repository.getEndBranchLabels().get(i);
            GEMHazardCurveRepository set = repository.getHcRepList().get(i);

            for (int k = 0; k < set.getGridNode().size(); k++)
            {
                Site site = set.getGridNode().get(k);

                // extracting needed values from the repository
                HazardCurveDTO hazardCurve = new HazardCurveDTO(site
                        .getLocation().getLongitude(), site.getLocation()
                        .getLatitude(), set.getGmLevels(), Arrays.asList(set
                        .getProbExceedanceList(k)), set
                        .getIntensityMeasureType(), set.getTimeSpan(),
                        endBranchLabel);

                System.out.println(hazardCurve.toJSON());
                
                serialize(hazardCurve);
            }
        }
    }

}
