package org.opensha.gem.GEM1.calc.gemOutput;

import java.util.ArrayList;
import java.util.List;

import org.opensha.commons.calc.ProbabilityMassFunctionCalc;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;

public class GEMHazardCurveRepository extends GEMHazardResults {

    // Sites on which the hazard curves have been computed
    private ArrayList<Site> gridNode;
    // Ground motion levels used to create the hazard curves (X values)
    private List<Double> gmLevels;
    // Y values of the Hazard curves
    private List<Double[]> probList;
    // GM values unit of measure
    private String unitsMeas;
    // intensity measure type
    private String intensityMeasureType;
    // time span duration
    private double timeSpan;

    /**
     * Constructor
     * 
     */
    public GEMHazardCurveRepository() {
        this.gridNode = new ArrayList<Site>();
        this.gmLevels = new ArrayList<Double>();
        this.probList = new ArrayList<Double[]>();
        this.unitsMeas = "";
        this.intensityMeasureType = "";
    }

    /**
     * Constructor
     * 
     * @param gmLev
     * @param unit
     */
    public GEMHazardCurveRepository(ArrayList<Double> gmLev, String unit) {
        this.gridNode = new ArrayList<Site>();
        this.gmLevels = gmLev;
        this.probList = new ArrayList<Double[]>();
        this.unitsMeas = unit;
        this.intensityMeasureType = "";
    }

    /**
     * Constructor
     * 
     * @param nodes
     * @param gmLev
     * @param probEx
     * @param unit
     */
    public GEMHazardCurveRepository(ArrayList<Site> nodes,
            ArrayList<Double> gmLev, ArrayList<Double[]> probEx, String unit) {
        this.gridNode = nodes;
        this.gmLevels = gmLev;
        this.probList = probEx;
        this.unitsMeas = unit;
        this.intensityMeasureType = "";
    }

    public void setIntensityMeasureType(String str) {
        this.intensityMeasureType = str;
    }

    public String getIntensityMeasureType() {
        return this.intensityMeasureType;
    }

    /**
     * This method return the probabilities of exceedance for set of GM values
     * at a given site (specified via 'idx')
     * 
     * @param idx
     * @return
     */
    public Double[] getProbExceedanceList(int idx) {
        return this.probList.get(idx);
    }

    /**
     * This method updates the content relative to a grid node by setting the
     * coordinates and the Y values of the hazard curve.
     * 
     * @param idx
     * @param lat
     * @param lon
     * @param probEx
     */
    public void setHazardCurveGridNode(int idx, double lat, double lon,
            Double[] probEx) {
        // gridNode.add(idx,new Site(new Location(lat,lon)));
        // probExList.add(idx, probEx);
        // gridNode.add(new Site(new Location(lat,lon)));
        // probExList.add(probEx);
        probList.set(idx, probEx);
    }

    public void addHazardCurveGridNode(int idx, double lat, double lon,
            Double[] probEx) {
        gridNode.add(idx, new Site(new Location(lat, lon)));
        probList.add(idx, probEx);
        // gridNode.add(new Site(new Location(lat,lon)));
        // probExList.add(probEx);
        // probExList.set(idx, probEx);
    }

    /**
     * 
     * @param idx
     * @param pex
     */
    public void update(int idx, Double[] pex) {

        if (probList.get(idx).length > 1) {
            Double[] tmp = probList.get(idx);
            for (int i = 0; i < pex.length; i++) {
                pex[i] = tmp[i] + pex[i];
            }
        }

        probList.set(idx, pex);
    }

    /**
     * This method computes a hazard map for a given probability of exceedance
     * using the hazard curves contained in the HazardCurveRepository
     * 
     * @param probExcedance
     * @return
     */
    public ArrayList<Double> getHazardMap(double probExcedance) {
        ArrayList<Double> hazardMap = new ArrayList<Double>();

        for (int i = 0; i < probList.size(); i++) {
            ArbitrarilyDiscretizedFunc fun = new ArbitrarilyDiscretizedFunc();
            Double[] tmp = probList.get(i);

            for (int j = 0; j < gmLevels.size(); j++) {
                fun.set(gmLevels.get(j), tmp[j]);
            }

            if (fun.getMaxY() < probExcedance) {
                hazardMap.add(0.0);
            } else if (fun.getMinY() > probExcedance) {
                hazardMap.add(Math.exp(fun.getMaxX()));
            } else {
                hazardMap
                        .add(Math.exp(fun.getFirstInterpolatedX(probExcedance)));
            }

        }
        return hazardMap;
    }

    /**
     * Computes the PMFs and updates the current set of hazard curves.
     */
    public void computePMFs() {
        List<Double[]> probOccs = new ArrayList<Double[]>();

        ArbitrarilyDiscretizedFunc PMF = null;

        for (int i = 0; i < getProbList().size(); i++) {
            PMF = ProbabilityMassFunctionCalc.getPMF(discretizedFunctionAt(i));
            probOccs.add(PMF.getYVals());
        }

        // gm levels are always the same, get the last one
        setGmLevels(PMF.getXVals());
        setProbList(probOccs);
    }

    /**
     * Returns an hazard curve as discretized function (OpenSHA model).
     * 
     * @param index
     *            the index of the curve to lookup
     * @return the discretized function representing this hazard curve
     */
    private ArbitrarilyDiscretizedFunc discretizedFunctionAt(int index) {
        Double[] probs = probList.get(index);
        ArbitrarilyDiscretizedFunc result = new ArbitrarilyDiscretizedFunc();

        for (int i = 0; i < probs.length; i++) {
            result.set(getGmLevels().get(i), probs[i]);
        }

        return result;
    }

    /**
     * Return the number of nodes on which an hazard curve is available
     * 
     * @return
     */
    public int getNodesNumber() {
        return this.gridNode.size();
    }

    public ArrayList<Site> getGridNode() {
        return gridNode;
    }

    public void setGridNode(ArrayList<Site> gridNode) {
        this.gridNode = gridNode;
    }

    public List<Double> getGmLevels() {
        return gmLevels;
    }

    private void setGmLevels(double[] gmLevels) {
        this.gmLevels = new ArrayList<Double>();

        for (double gmLevel : gmLevels) {
            this.gmLevels.add(gmLevel);
        }
    }

    public void setGmLevels(ArrayList<Double> gmLevels) {
        this.gmLevels = gmLevels;
    }

    public List<Double[]> getProbList() {
        return probList;
    }

    public void setProbList(List<Double[]> probList) {
        this.probList = probList;
    }

    public String getUnitsMeas() {
        return unitsMeas;
    }

    public void setUnitsMeas(String unitsMeas) {
        this.unitsMeas = unitsMeas;
    }

    public double getTimeSpan() {
        return timeSpan;
    }

    public void setTimeSpan(double timeSpan) {
        this.timeSpan = timeSpan;
    }

}
