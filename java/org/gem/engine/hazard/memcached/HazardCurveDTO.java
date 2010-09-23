package org.gem.engine.hazard.memcached;

import java.util.List;

import com.google.gson.Gson;

/**
 * A simple data transfer object that contains the hazard curve
 * data used in the serialization process.
 * <p>
 * This object resizes in this little serialization layer and
 * it is not part of the hazard engine object model.
 * 
 * @author Andrea Cerisara
 */
public class HazardCurveDTO
{

    private Double latitude;
    private Double longitude;

    private List<Double> groundMotionLevels;
    private List<Double> probabilitiesOfExc;

    /**
     * Main constructor.
     * <p>
     * X and Y values are ordered in the same way, i.e. if I get the X value
     * at index i, the related Y values is itself at index i as well.
     * 
     * @param longitude the longitude of the site of this curve
     * @param latitude the latitude of the site of this curve
     * @param groundMotionLevels ground motion values of this curve (X values)
     * @param probabilitiesOfExc probabilities of exceedance
     * of this curve (Y values)
     */
    public HazardCurveDTO(Double longitude, Double latitude,
            List<Double> groundMotionLevels, List<Double> probabilitiesOfExc)
    {
        this.latitude = latitude;
        this.longitude = longitude;

        this.groundMotionLevels = groundMotionLevels;
        this.probabilitiesOfExc = probabilitiesOfExc;
    }

    /**
     * Not used, needed by the JSON serialization library.
     */
    public HazardCurveDTO()
    {
        // TODO Needed by JSON library
    }

    /**
     * Returns the longitude of the site of this curve.
     * 
     * @return the longitude of the site of this curve
     */
    public Double getLongitude()
    {
        return longitude;
    }

    /**
     * Returns the latitude of the site of this curve.
     * 
     * @return the latitude of the site of this curve
     */
    public Double getLatitude()
    {
        return latitude;
    }

    /**
     * Returns a JSON representation of this curve.
     * 
     * @return a string containing a JSON representation of this curve
     */
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
        return other.longitude.equals(longitude)
                && other.latitude.equals(latitude);
    }

    private boolean sameValues(HazardCurveDTO other)
    {
        return other.groundMotionLevels.equals(groundMotionLevels)
                && other.probabilitiesOfExc.equals(probabilitiesOfExc);
    }

}
