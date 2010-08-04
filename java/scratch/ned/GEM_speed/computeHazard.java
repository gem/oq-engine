package scratch.ned.GEM_speed;

import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.rupForecastImpl.GEM.TestGEM_ERF;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;


public class computeHazard implements Runnable {
	
	private class computeHazardRange{
		public int start, end;
	}
	
	// array storing pga values
	private double pga[];
	
	// list of sites where to compute hazard curve
	public ArrayList<Site> siteList;
	
	// number of threads
	private Thread pgaThreads[];
	private int startLoop, endLoop, curLoop, numThreads;	
	
	// constructor
	public computeHazard(int npgaLat,int npgaLon, int nproc, ArrayList<Site> _siteList){
		
		pga = new double[npgaLat*npgaLon];
		
		siteList = _siteList;
		
		pgaThreads = new Thread[nproc];
		
		startLoop = curLoop = 0;
		endLoop = npgaLat*npgaLon;
		
		numThreads = nproc;

		
	}
	
	private synchronized computeHazardRange loopGetRange(){
		if (curLoop >= endLoop)
			return null;
		
		computeHazardRange r = new computeHazardRange();
		
		r.start = curLoop;
		
		// each thread execute only one hazard calculation
//		curLoop += 1;//(endLoop-startLoop)/numThreads+1;
		curLoop += (endLoop-startLoop)/numThreads+1;
		
		r.end = (curLoop<endLoop)?curLoop:endLoop;
		
		return r;
		
	}
	
	private void loopDoRange(int start, int end){
		
		System.out.println("started loopDoRange"+"\t"+start+"\t"+end);
/*		
    	// intensity measure level
	    ArbitrarilyDiscretizedFunc hc = new ArbitrarilyDiscretizedFunc();
	    hc.set(0.00010,1);
	    hc.set(0.00013,1);
		hc.set(0.00016,1);
		hc.set(0.00020,1);
		hc.set(0.00025,1);
		hc.set(0.00032,1);
		hc.set(0.00040,1);
		hc.set(0.00050,1);
		hc.set(0.00063,1);
		hc.set(0.00079,1);
		hc.set(0.00100,1);
		hc.set(0.00126,1);
		hc.set(0.00158,1);
		hc.set(0.00200,1);
		hc.set(0.00251,1);
		hc.set(0.00316,1);
		hc.set(0.00398,1);
		hc.set(0.00501,1);
		hc.set(0.00631,1);
		hc.set(0.00794,1);
		hc.set(0.01000,1);
		hc.set(0.01259,1);
		hc.set(0.01585,1);
		hc.set(0.01995,1);
		hc.set(0.02512,1);
		hc.set(0.03162,1);
		hc.set(0.03981,1);
		hc.set(0.05012,1);
		hc.set(0.0631,1);
		hc.set(0.07943,1);
	    hc.set(0.10000,1);
		hc.set(0.12589,1);
		hc.set(0.15849,1);
		hc.set(0.19953,1);
		hc.set(0.25119,1);
		hc.set(0.31623,1);
		hc.set(0.39811,1);
		hc.set(0.50119,1);
		hc.set(0.63096,1);
		hc.set(0.79433,1);
		hc.set(1.00000,1);
		hc.set(1.25893,1);
		hc.set(1.58489,1);
		hc.set(1.99526,1);
		hc.set(2.51189,1);
		hc.set(3.16228,1);
		hc.set(3.98107,1);
		hc.set(5.01187,1);
		hc.set(6.30957,1);
		hc.set(7.94328,1);
		hc.set(10.0,1);	
	    for(int in=0;in<hc.getNum();in++) hc.set(Math.log(hc.getX(in)), hc.getY(in));
*/	    
/*	 */   
	    ArbitrarilyDiscretizedFunc hc = new ArbitrarilyDiscretizedFunc();
	    hc.set(0.0050,1);
//	    hc.set(0.0070,1);
//	    hc.set(0.0098,1);
//	    hc.set(0.0137,1);
//	    hc.set(0.0192,1);
//	    hc.set(0.0269,1);
//	    hc.set(0.0376,1);
//	    hc.set(0.0527,1);
//	    hc.set(0.0738,1);
//	    hc.set(0.103,1);
//	    hc.set(0.145,1);
//	    hc.set(0.203,1);
//	    hc.set(0.284,1);
//	    hc.set(0.397,1);
//	    hc.set(0.556,1);
//	    hc.set(0.778,1);
//	    hc.set(1.09,1);
//	    hc.set(1.52,1);
//	    hc.set(2.13,1);
	    for(int in=0;in<hc.getNum();in++) hc.set(Math.log(hc.getX(in)), hc.getY(in));
    
	    
	    // attenuation relationship (Abrahmson and Silva 1997)
        AS_1997_AttenRel as_1997;
	    ParameterChangeWarningEvent event = null;
	    as_1997 = new AS_1997_AttenRel(ParameterChangeWarningListener(event));
	    as_1997.setParamDefaults();
	    // Define intensity measure type
	    as_1997.setIntensityMeasure("PGA");
        
        // truncation level
        as_1997.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_2SIDED);
        
        // hazard curve calculator
        HazardCurveCalculator hcc;
        
		// time span
		TimeSpan time = new TimeSpan(TimeSpan.YEARS,TimeSpan.YEARS);
		time.setDuration(50,TimeSpan.YEARS);
		
		// probability value for computing PGA
		double prob_level = 0.1;
		
		// ERF
		TestGEM_ERF sszERF = new TestGEM_ERF();
		
/*		
		// ERF 
		SeismicZoneERF sszERF = null;
		
		// define ERF for seismic source zones
		
		// file containing seismic source specifications
		//String SSZfname = "/Users/damianomonelli/Documents/GEM/openSHA/ComputationTime/SEAssz.dat";
		String SSZfname = "/Users/field/workspace/OpenSHA/dev/scratch/ned/GEM_speed/SEAssz.dat.txt";
		// Seismic Zone object
		SeismicZone ssz = new SeismicZone(SSZfname);
		
	    // average rake and dip inside each seismic zone
		double rake = 0.0;
		double dip = 90.0;
		
		// grid spacing inside seismic source zone
		double gridspacing = 0.05;
		// magnitude bin width for GR magnitude frequency distribution
		double mbin = 0.1;
        
		// total number of ruptures
		int ntotrup = 0;
		
		// earthquake rupture forecast for all ssz
		//SeismicZoneERF sszERF = new SeismicZoneERF();
		sszERF = new SeismicZoneERF();
		
		// loop over seismic zones
		for(int ii=0;ii<ssz.getA().size();ii++){
			// define polygon region
			GriddedRegion gr = new GriddedRegion(ssz.getPoly().get(ii),gridspacing);
			// define GR magnitude-frequency distribution
			// number of magnitude values
			int mnum = (int) Math.round((ssz.getMmax().get(ii)-ssz.getMmin().get(ii))/mbin)+1;
			// GR law
			GutenbergRichterMagFreqDist GRmfd2 = new GutenbergRichterMagFreqDist(ssz.getMmin().get(ii).doubleValue(),ssz.getMmax().get(ii).doubleValue(),mnum);
			for(int igr=0;igr<mnum;igr++){
				GRmfd2.set(igr, Math.pow(10,ssz.getA().get(ii).doubleValue()-ssz.getB().get(ii).doubleValue()*GRmfd2.getX(igr)));
			}

			GriddedRegionPoissonEqkSource sszEqkSource = new GriddedRegionPoissonEqkSource(gr,GRmfd2,time.getDuration(),rake,dip);
			sszERF.addSource(sszEqkSource);
			ntotrup = ntotrup+sszEqkSource.getNumRuptures();
		}
*/
		
		long origStartTime = System.currentTimeMillis();
		
				
		// loop over sites where to compute hazard
		for(int i=start; i<end;i+=1){
//		for(int i=26; i<=26;i+=1){
			
			
			// start timing
			long startTime = System.currentTimeMillis();
			
			/**/
			//initialize site parameters for attenuation relation
			for(int is=0;is<siteList.size();is++){
				// set site parameters
				ListIterator<ParameterAPI<?>> it = as_1997.getSiteParamsIterator();
		        while (it.hasNext()) {
			           ParameterAPI param = it.next();
			           if (!siteList.get(i).containsParameter(param))
				           siteList.get(i).addParameter(param);
		        }
			}
			
//			System.out.println("starting hazard calc");
				        
    		// perform hazard calculation
		    try {
		        // define hazard calculator
			    hcc = new HazardCurveCalculator();
			    // compute hazard curve
				hcc.getHazardCurve(hc,siteList.get(i),as_1997,sszERF);
                // store pga value corresponding to the chosen probability
                if(hc.getY(0)<prob_level){
                	pga[i] = 0;
                }
                else{
//				pga[i] = Math.exp(hc.getFirstInterpolatedX(prob_level));
                }
    			// start timing
    			long endTime = System.currentTimeMillis();
    			double compSecs = (endTime-startTime)/1e3;
    			double aveCompSecs = (endTime-origStartTime)/1e3/(i+1);
                System.out.println("Node "+(i-start)+", of "+(end-start)+", "+siteList.get(i).getLocation()+", PGA: "+pga[i]+", compTime: "+compSecs+", aveCompTime: "+aveCompSecs);
                //System.out.println("Thread: "+(start-startLoop)/(end-start)+", Node "+(i-start)+", of "+(end-start)+", "+siteList.get(i).getLocation()+", PGA: "+pga[i]);
			} catch (RemoteException e) {
				e.printStackTrace();
			}
	        			
		}
		
	}

	public void run() {
		
		computeHazardRange range;
		
		while ( (range=loopGetRange())!=null){
			loopDoRange(range.start,range.end);
		}
		
	}
	
	public double[] getValues(){
		for(int i=0;i<numThreads;i++){
			pgaThreads[i] = new Thread(this);
			pgaThreads[i].start();
		}
		for(int i=0;i<numThreads;i++){
			try{
				pgaThreads[i].join();
			} catch (InterruptedException iex) {}
		}
		return pga;
	}
	
	private static ParameterChangeWarningListener ParameterChangeWarningListener(
			ParameterChangeWarningEvent event) {
		return null;
	}

}
