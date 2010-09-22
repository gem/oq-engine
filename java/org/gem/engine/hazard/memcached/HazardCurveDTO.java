package org.gem.engine.hazard.memcached;

import java.util.List;

import com.google.gson.Gson;

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
