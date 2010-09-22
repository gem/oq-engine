package org.gem.engine.hazard.memcached;

import java.util.List;

import com.google.gson.Gson;

/**
 * A simple data transfer object that contains the hazard curve data used in the serialization process.
 * 
 * I created a new object because:
 * 
 * - didn't want to modify the hazard engine API
 * - dint't want to serialize all the data present in the hazard engine API objects
 * - the conversion cost should be low
 * - made testing easier
 * 
 * This object resizes in this little serialization layer and it is not part of the hazard engine object model.
 * 
 * Any feedback about designing this stuff is welcome :-)
 * 
 * @author Andrea Cerisara
 */
public class HazardCurveDTO
{

    private Double lon;
    private Double lat;

    private List<Double> groundMotionLevels;
    private List<Double> probabilitiesOfExc;

    public HazardCurveDTO(Double lon, Double lat, List<Double> groundMotionLevels, List<Double> probabilitiesOfExc)
    {
        this.lon = lon;
        this.lat = lat;

        this.groundMotionLevels = groundMotionLevels;
        this.probabilitiesOfExc = probabilitiesOfExc;
    }

    public HazardCurveDTO()
    {
        // TODO Auto-generated constructor stub
    }

    public String toJSON()
    {
        return new Gson().toJson(this);
    }

    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof HazardCurveDTO))
        {
            return false;
        }

        HazardCurveDTO other = (HazardCurveDTO) obj;

        return sameSite(other) && sameValues(other);
    }

    private boolean sameSite(HazardCurveDTO other)
    {
        return other.lon.equals(lon) && other.lat.equals(lat);
    }

    private boolean sameValues(HazardCurveDTO other)
    {
        return other.groundMotionLevels.equals(groundMotionLevels)
                && other.probabilitiesOfExc.equals(probabilitiesOfExc);
    }

}
