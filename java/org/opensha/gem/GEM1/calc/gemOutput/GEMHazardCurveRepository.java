package org.opensha.gem.GEM1.calc.gemOutput;

import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;

public class GEMHazardCurveRepository extends GEMHazardResults {

	// Sites on which the hazard curves have been computed
	private ArrayList<Site> gridNode;
	// Ground motion levels used to create the hazard curves (X values)
	private ArrayList<Double> gmLevels;			
	// Y values of the Hazard curves 
	private ArrayList<Double[]> probExList; 
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
	public GEMHazardCurveRepository(){
		this.gridNode = new ArrayList<Site>();
		this.gmLevels = new ArrayList<Double>();
		this.probExList = new ArrayList<Double[]>();
		this.unitsMeas = "";
		this.intensityMeasureType = "";
	}
	
	/**
	 * Constructor
	 * 
	 * @param gmLev
	 * @param unit
	 */
	public GEMHazardCurveRepository(ArrayList<Double> gmLev, String unit){
		this.gridNode = new ArrayList<Site>();
		this.gmLevels = gmLev;
		this.probExList = new ArrayList<Double[]>();
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
	public GEMHazardCurveRepository(ArrayList<Site> nodes, ArrayList<Double> gmLev, ArrayList<Double[]> probEx, String unit){
		this.gridNode = nodes;
		this.gmLevels = gmLev;
		this.probExList = probEx;
		this.unitsMeas = unit;
		this.intensityMeasureType = "";
	}
	
	public void setIntensityMeasureType(String str){
		this.intensityMeasureType = str;
	}
	
	public String getIntensityMeasureType(){
		return this.intensityMeasureType;
	}
	
	/**
	 * This method return the probabilities of exceedance for set of GM values at a given site 
	 * (specified via 'idx')
	 * 
	 * @param idx
	 * @return
	 */
	public Double[] getProbExceedanceList(int idx) {
		return this.probExList.get(idx);
	}
	
	/**
	 * This method updates the content relative to a grid node by setting the coordinates and the 
	 * Y values of the hazard curve.
	 * 
	 * @param idx
	 * @param lat
	 * @param lon
	 * @param probEx
	 */
	public void setHazardCurveGridNode(int idx, double lat, double lon, Double[] probEx){
//		gridNode.add(idx,new Site(new Location(lat,lon)));
//		probExList.add(idx, probEx);
//		gridNode.add(new Site(new Location(lat,lon)));
//		probExList.add(probEx);
		probExList.set(idx, probEx);
	}
	
	public void addHazardCurveGridNode(int idx, double lat, double lon, Double[] probEx){
		gridNode.add(idx,new Site(new Location(lat,lon)));
		probExList.add(idx, probEx);
//		gridNode.add(new Site(new Location(lat,lon)));
//		probExList.add(probEx);		
		//probExList.set(idx, probEx);
	}
	
	/**
	 * 
	 * @param idx
	 * @param pex
	 */
	public void update(int idx, Double[] pex){
				
		if (probExList.get(idx).length > 1){
			Double[] tmp = probExList.get(idx);
			for (int i=0; i<pex.length; i++){
				pex[i] = tmp[i] + pex[i];
			}
		}

		probExList.set(idx, pex);
	}
	
	/**
	 * This method computes a hazard map for a given probability of exceedance using
	 * the hazard curves contained in the HazardCurveRepository
	 * 
	 * @param probExcedance
	 * @return
	 */
	public ArrayList<Double> getHazardMap (double probExcedance){
		ArrayList<Double> hazardMap = new ArrayList<Double>();

		for (int i=0; i<probExList.size(); i++ ){
			ArbitrarilyDiscretizedFunc fun = new ArbitrarilyDiscretizedFunc();
			Double[] tmp = probExList.get(i);

			for (int j = 0; j<gmLevels.size(); j++){
				fun.set(gmLevels.get(j),tmp[j]);
			}
			
            if (fun.getMaxY()<probExcedance){
            	hazardMap.add(0.0);
            } else if(fun.getMinY()>probExcedance){
            	hazardMap.add(Math.exp(fun.getMaxX()));
            } else{
            	hazardMap.add(Math.exp(fun.getFirstInterpolatedX(probExcedance)));
            }    
			
		}
		return hazardMap;
	}
	
	/**
	 * Return the number of nodes on which an hazard curve is available
	 * @return
	 */
	public int getNodesNumber(){
		return this.gridNode.size();
	}
	
	/**
	 * 
	 * @return
	 */
	public ArrayList<Site> getGridNode() {
		return gridNode;
	}
	public void setGridNode(ArrayList<Site> gridNode) {
		this.gridNode = gridNode;
	}
	public ArrayList<Double> getGmLevels() {
		return gmLevels;
	}
	public void setGmLevels(ArrayList<Double> gmLevels) {
		this.gmLevels = gmLevels;
	}
	public ArrayList<Double[]> getProbExList() {
		return probExList;
	}
	public void setProbExList(ArrayList<Double[]> probEx) {
		this.probExList = probEx;
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
