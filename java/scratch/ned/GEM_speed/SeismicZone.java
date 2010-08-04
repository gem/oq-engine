package scratch.ned.GEM_speed;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class SeismicZone {
	
	// a value
	private ArrayList<Double> a;
	// b value
	private ArrayList<Double> b;
	// minimum magnitude
	private ArrayList<Double> mmin;
	// maximum magnitude
	private ArrayList<Double> mmax;
	// polygon coordinates
	private ArrayList<LocationList> poly; 
	
	// Methods
	
	// return a values
	public ArrayList<Double> getA(){
		return a;
	}
	
	// return b values
	public ArrayList<Double> getB(){
		return b;
	}
	
	// return minimum magnitude
	public ArrayList<Double> getMmin(){
		return mmin;
	}
	
	// return maximum magnitude
	public ArrayList<Double> getMmax(){
		return mmax;
	}
	
	// return polygon coordinates
	public ArrayList<LocationList> getPoly(){
		return poly;
	}
	
	// Constructor
	
	// the argument is:
	// SSZfname: the path to the seismic zones file
	public SeismicZone(String SSZfname){

		a = new ArrayList<Double>();
		b = new ArrayList<Double>();
		mmin = new ArrayList<Double>();
		mmax = new ArrayList<Double>();
		poly = new ArrayList<LocationList>();
		
		
		// read the seismicity rate file
        try {
            String sRecord = null;
            StringTokenizer st = null;
            int i;
            Double A;
            Double B;
            Double MMIN;
            Double MMAX;
            Double LAT;
            Double LON;
            LocationList POLY = null;

            // Get a handle to the file
            FileInputStream oFIS = new FileInputStream(SSZfname);
            BufferedInputStream oBIS = new BufferedInputStream(oFIS);
            BufferedReader oReader = new BufferedReader(new InputStreamReader(oBIS));

            // pass through the file
            int is = 0;
            while ((sRecord = oReader.readLine()) != null) {
            	st = new StringTokenizer(sRecord);
            	// a value
            	A = Double.valueOf(st.nextToken());
            	// b value
            	B = Double.valueOf(st.nextToken());
            	// minimum magnitude
            	MMIN = Double.valueOf(st.nextToken());
            	// maximum magnitude
            	MMAX = Double.valueOf(st.nextToken());
            	// polygon vertices
            	POLY = new LocationList();
            	i = 0;
            	while (st.hasMoreTokens()) {
            		LAT = Double.valueOf(st.nextToken());
            		LON = Double.valueOf(st.nextToken());
            		POLY.add(i, new Location(LAT.doubleValue(),LON.doubleValue()));
                	i = i+1;
                }
            	a.add(is, A);
            	b.add(is, B);
            	mmin.add(is, MMIN);
            	mmax.add(is,MMAX);
            	poly.add(is,POLY);
            	is = is+1;
            }

            oReader.close();
            oReader = null;
            oBIS.close();
            oBIS = null;
            oFIS.close();
            oFIS = null;
        } catch (Exception ex) {
            System.err.println("Trouble reading seismicity rates file in " + SSZfname);
            ex.printStackTrace();
            System.exit(-1);
        }

    }

}
