package scratch.ned.GEM_speed;

import java.util.ArrayList;

import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;

public class SeismicZoneERF extends EqkRupForecast{

	
    private static String  C = "SeismicZoneERF";
	private ArrayList<ProbEqkSource> allSources = null;
	
	// No argument constructor
	public SeismicZoneERF(){
	allSources = new ArrayList<ProbEqkSource>();
	}
	
	// add source
	public void addSource(GriddedRegionPoissonEqkSource grpes){
		allSources.add(grpes);
	}

	// number of sources
	public int getNumSources() {
		return allSources.size();
	}

	// return source at index source
	public ProbEqkSource getSource(int source) {
		return allSources.get(source);
	}

	// return list of sources
	public ArrayList getSourceList() {
		return allSources;
	}

	// return name of the class
	public String getName() {
		return C;
	}

	public void updateForecast() {
		return;
	}
}
