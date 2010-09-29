package org.opensha.sha.calc.stochasticEventSet;

import java.io.BufferedWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class SeismHist {
	
	private ArrayList<Double> tOcc;
	private ArrayList<ProbEqkRupture> rupt; 

	/**
	 * This is a very basic constructor 
	 */
	public SeismHist() {
		this.tOcc = new ArrayList<Double>();
		this.rupt = new ArrayList<ProbEqkRupture>();
	}
	
	/**
	 * This is a second constructor 
	 * @param tOcc			Array list with the time of occurrence of each event
	 * @param rupt			Array list with the ruptures composing the seismicity history
	 */
	public SeismHist(ArrayList<Double> tOcc, ArrayList<ProbEqkRupture> rupt) {
		this.tOcc = tOcc;
		this.rupt = rupt;
	}

	/**
	 * This method add a new event to the seismicity history
	 * @param time			Time of occurrence
	 * @param rupt			Probabilistic Earthquake Rupture
	 */
	public void addEvent(double time, ProbEqkRupture rupt){
		this.tOcc.add(time);
		this.rupt.add(rupt);
	}	
	
	/**
	 * This method provides the list of time of occurrence 
	 * @return tOcc			Array list with the time of occurrence of each event
	 */
	public ArrayList<Double> getTimeOcc(){
		return this.tOcc;
	}
	
	/**
	 * This method provides the list of ruptures composing the seismicity history 
	 * @return rupt			Array list with the ruptures composing this seismicity history
	 */
	public ArrayList<ProbEqkRupture> getRuptures(){
		return this.rupt;
	}
	
	/**
	 * 
	 * @return 				Number of events contained in the seismicity history
	 */
	public int getNumRuptures() {
		return this.rupt.size();
	}
	
	/**
	 * 
	 * @return 				PrbEqkRupture
	 */
	public ProbEqkRupture getRupture(int idx) {
		return this.rupt.get(idx);
	}
	
	/**
	 * 
	 * @param outBuf
	 * @throws IOException  
	 */
	public void writeRuptures(BufferedWriter outBuf) throws IOException {
		for (ProbEqkRupture rup: rupt){
			outBuf.write(String.format("> -G%.0f/%.0f/%.0f\n", Math.random()*255,Math.random()*255,Math.random()*255));
			EvenlyGriddedSurfaceAPI rupSurf =  rup.getRuptureSurface();
			// Loop over the left side of the rupture
			for (int i=0; i < rupSurf.getNumRows(); i++){
				outBuf.write(String.format("%+7.4f %+6.4f %6.2f\n",
					rupSurf.getLocation(i,0).getLongitude(),
					rupSurf.getLocation(i,0).getLatitude(),
					rupSurf.getLocation(i,0).getDepth()*-1.0
					));
			}	 
			// Loop over the bottom side of the rupture
			for (int i=0; i < rupSurf.getNumCols(); i++){
				outBuf.write(String.format("%+7.4f %+6.4f %6.2f\n",
					rupSurf.getLocation(rupSurf.getNumRows()-1,i).getLongitude(),
					rupSurf.getLocation(rupSurf.getNumRows()-1,i).getLatitude(),
					rupSurf.getLocation(rupSurf.getNumRows()-1,i).getDepth()*-1.0
					));
			 } 
			// Loop over the right side of the rupture
//			for (int i=0; i < rupSurf.getNumRows(); i++){
			for (int i=rupSurf.getNumRows()-1; i>=0; i--){
				outBuf.write(String.format("%+7.4f %+6.4f %6.2f\n",
					rupSurf.getLocation(i,rupSurf.getNumCols()-1).getLongitude(),
					rupSurf.getLocation(i,rupSurf.getNumCols()-1).getLatitude(),
					rupSurf.getLocation(i,rupSurf.getNumCols()-1).getDepth()*-1.0
					));
			}
			// Loop over the top side of the rupture
//			for (int i=0; i < rupSurf.getNumCols(); i++){
			for (int i=rupSurf.getNumCols()-1; i>=0; i--){
				outBuf.write(String.format("%+7.4f %+6.4f %6.2f\n",
					rupSurf.getLocation(0,i).getLongitude(),
					rupSurf.getLocation(0,i).getLatitude(), 
					rupSurf.getLocation(0,i).getDepth()*-1.0
					)); 
			}
			
		}
	}
}
