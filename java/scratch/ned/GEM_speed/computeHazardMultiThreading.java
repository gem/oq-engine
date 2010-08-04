package scratch.ned.GEM_speed;

import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;


public class computeHazardMultiThreading {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		
		// start timing
		long start = System.currentTimeMillis();	
		
		// region where to compute hazard
        double latmin = 25.0;
        double latmax = 45.0;
        double lonmin = 60.0;
        double lonmax = 95.0;
        double delta = 5;
    
        // total number of nodes in latitude and longitude direction
	    int npgaLat = (int)((latmax-latmin)/delta)+1;
	    int npgaLon = (int)((lonmax-lonmin)/delta)+1;
	    
	    System.out.println("Total number of nodes where to compute hazard: "+npgaLat*npgaLon);
	    
	    // list of sites where to compute hazard
	    ArrayList<Site> hazSite = new ArrayList<Site>();
	    int ii = 0;
        for (int i=0;i<npgaLat;i++) {
            for (int j=0;j<npgaLon;j++) {
	    	hazSite.add(ii,new Site(new Location(latmin+delta*i,lonmin+delta*j)));
	    	ii = ii+1;
            }
        }
        
        // number of threads
        int nproc =1;
        
        // define computeHazard object
        computeHazard ch = new computeHazard(npgaLat,npgaLon,nproc,hazSite);
        
        // pga values
        double[] pga = new double[npgaLat*npgaLon];
        // compute pga values
        pga = ch.getValues();
        
        // stop timing
        long stop = System.currentTimeMillis();
        // print execution time
        System.out.println("Final execution time: " + (stop - start)/(Math.pow(10.0, 3.0)*60) + " minutes");
        
        
		// output PGA values
        //String outputFilePath = "/Users/damianomonelli/Documents/GEM/openSHA/SEA/SEAssz_pga2.dat";
        //String outputFilePath = "/Users/damianomonelli/Documents/GEM/openSHA/ComputationTime/SEAssz_pga.dat";
//        String outputFilePath = "/home/damiano/Test/results/SEA/SEAssz_PGA01.dat";
        String outputFilePath = "/Users/field/workspace/OpenSHA/dev/scratch/ned/GEM_speed/SEAssz_PGA01.txt";
        try {
            FileOutputStream oOutFIS = new FileOutputStream(outputFilePath);
            BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
            BufferedWriter oWriter = new BufferedWriter(new OutputStreamWriter(oOutBIS));

            int in = 0;
            for (int i=0;i<npgaLat;i++) {
                for (int j=0;j<npgaLon;j++) {
                	oWriter.write((float)(lonmin+delta*j) + " " + (float)(latmin+delta*i) + " " + pga[in] + "\n");
                	in = in+1;
                }
            }

            oWriter.close();
            oOutBIS.close();
            oOutFIS.close();
        } catch (Exception ex) {
            System.err.println("Trouble generating PGA file");
            ex.printStackTrace();
            System.exit(-1);
        }
        System.exit(0);

	}

}
