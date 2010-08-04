package org.opensha.gem.GEM1.scratch.testGmpe;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.gem.GEM1.scratch.AtkBoo_2006_AttenRel;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.StressDropParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class Verify_AtkBoo_2006 {
	
	public static void main(String[] args) {
		
		boolean OLD_VERIFICATION = true;
		boolean SPECTRA_CALC = false;
		
		double aveDip = 90.0;
        double lowerSeisDepth = 5.0;
        double upperSeisDept = 10.0;
        double rake = 90.0;
        String fle;
        ArrayList<Double[]> dat;
        
		// Repository
		String dir = "org/opensha/sha/earthquake/rupForecastImpl/GEM1/scratch/testGmpe/verification_Tables_AtkBoo_2006/";
	
		// Instantiate the GMPE
		AtkBoo_2006_AttenRel imr = new AtkBoo_2006_AttenRel(null);   
		//AtkBoo_2006_AttenRel2 imr = new AtkBoo_2006_AttenRel2(null);   
        imr.setParamDefaults();
        
        // Create fault trace 
        FaultTrace ftrace = new FaultTrace("test");
        ftrace.add(new Location(45.00,10.00));
        ftrace.add(new Location(46.00,10.00));
        
        // Calculate magnitude from the fault trace 
        WC1994_MagLengthRelationship magLenRel = new WC1994_MagLengthRelationship();
        double mag = magLenRel.getMedianMag(ftrace.getTraceLength(),rake);
		
        // Create fault surface 
        SimpleFaultData fltDat =  new SimpleFaultData(aveDip,upperSeisDept,lowerSeisDepth,ftrace);
        StirlingGriddedSurface fltSurf = new StirlingGriddedSurface(fltDat,10.0);
		
        ((WarningDoubleParameter)imr.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(2200.0);
  
        //------------------------------------------------------------------------------------------
        //------------------------------------ Verification based on the most recent tables received 
        CheckGMPE1(imr,ReadTable1(dir+"ab06_output_for_comparisons_hr.out")); System.out.println("");
        CheckGMPE1(imr,ReadTable1(dir+"ab06_output_for_comparisons_soil.out"));
        
        //------------------------------------------------------------------------------------------
        //------------------------------------------------------- Verification based on older tables
        // NOTE: after receiving the new verification tables this wasn't used anymore!!
        if (OLD_VERIFICATION) {
		    // Read one input file - T=3.13s
		    // OK perfect
//		    imr.setIntensityMeasure(SA_Param.NAME);
//		    System.out.printf("\n Hard Rock: T=3.13s\n");
//		    imr.getParameter(PeriodParam.NAME).setValue(3.125);
//		  	CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_hr.f0.32.out"));	
			
//		    // Read one input file - T=1.0s
//		    // OK
//			System.out.printf("\n Hard Rock: T=1.00s\n");
//		    imr.setIntensityMeasure(SA_Param.NAME);
//		    imr.getParameter(PeriodParam.NAME).setValue(1.00);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_hr.f1.00.out"));	
			
		    // Read one input file - T=0.2s
		    // Some differences. Parameters checked 
//			System.out.printf("\n Hard Rock: T=0.20s\n");
//		    imr.setIntensityMeasure(SA_Param.NAME);
//		    imr.getParameter(PeriodParam.NAME).setValue(0.2);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_hr.f5.00.out"));	
			
		    // Read one input file - T=0.0s
			// OK some slight differences
//			System.out.printf("\n Hard Rock: PGA\n");
//		    imr.setIntensityMeasure(PGA_Param.NAME);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_hr.pga.out"));
			
		    // Read one input file - PGV
			// OK 
//			System.out.printf("\n Hard Rock: PGV\n");
//			imr.setIntensityMeasure(PGV_Param.NAME);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_hr.pgv.out"));
		
			// BC category
//			((WarningDoubleParameter)imr.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(760.0);
			
		    // Read one input file - T=3.13s
			// OK perfect
//		    imr.setIntensityMeasure(SA_Param.NAME);
//		    System.out.printf("\n BC Category: T=3.13s\n");
//		    imr.getParameter(PeriodParam.NAME).setValue(3.125);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_bc.f0.32.out"));	
			
		    // Read one input file - T=1.0s
			// OK with some slight differences
//			System.out.printf("\n BC Category: T=1.00s\n");
//		    imr.setIntensityMeasure(SA_Param.NAME);
//		    imr.getParameter(PeriodParam.NAME).setValue(1.00);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_bc.f1.00.out"));	
			
		    // Read one input file - T=0.2s
		    // Some differences. Parameters checked 
//			System.out.printf("\n BC Category: T=0.20s\n");
//		    imr.setIntensityMeasure(SA_Param.NAME);
//		    imr.getParameter(PeriodParam.NAME).setValue(0.2);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_bc.f5.00.out"));	
			
		    // Read one input file - T=0.0s
			// OK
//			System.out.printf("\n BC Category: PGA\n");
//		    imr.setIntensityMeasure(PGA_Param.NAME);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_bc.pga.out"));
			
		    // Read one input file - PGV
			// OK - controlled
//			System.out.printf("\n BC Category: PGV\n");
//			imr.setIntensityMeasure(PGV_Param.NAME);
//			CheckGMPE(imr,ReadTable(dir+"ab06_gm_vs_r_m5.5_7.5_bc.pgv.out"));
        }
		
        //------------------------------------------------------------------------------------------
        //---------------------------------------------------------------------- Spectra calculation
        if (SPECTRA_CALC) {
			// Compute spectrum
			double dst = 30;  
			mag = 5.5;
			double vs30 = 2100;
			System.out.printf("\n Spectrum m: %5.2f vs30: %6.2f \n",mag,vs30);
			((WarningDoubleParameter)imr.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mag));
			((WarningDoubleParameter)imr.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(vs30);
			ComputeSpectrum(imr,dst);
			
			// Compute spectrum
			dst = 30;  
			mag = 5.5;
			vs30 = 760;
			System.out.printf("\n Spectrum m: %5.2f vs30: %6.2f \n",mag,vs30);
			((WarningDoubleParameter)imr.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mag));
			((WarningDoubleParameter)imr.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(vs30);
			ComputeSpectrum(imr,dst);
        }
        
	}

	/**
	 * This reads the verification tables downloaded from the website of David Boore on February, 
	 * 2010. These files are in the repository directory named 'verification_Tables_AtkBoo_2006'. 
	 * The suffix used to identify these files is 'ab06_gm_vs_r_*'
	 * 
	 * @param flepath
	 * @return
	 */
	public static ArrayList<Double[]> ReadTable(String flepath){
		ArrayList<Double[]> dat = new ArrayList<Double[]>();
		String currentLine, line;
		String[] strArr;
		int cnt = 0;
		
		// Try to read 'flepath'
		try {
			// Open buffer
	    	BufferedReader input =  new BufferedReader(new FileReader(flepath));	
    		try {
    			// Read lines
    			while ((currentLine = input.readLine()) != null) {
    				cnt++;
    				if (cnt>1) {
    					// Split string after cleaning
    					line = currentLine.trim(); strArr = line.split("\\s+");
    					Double[] lineDat = new Double[strArr.length];		
    					for (int i = 0; i < strArr.length; i++){
    						lineDat[i] = Double.valueOf(strArr[i]).doubleValue();
    					}
    					dat.add(lineDat);
    				}
    			}
    		} finally {
		    	input.close();
	    	}
		} catch (FileNotFoundException e) {
    	      e.printStackTrace();
    	} catch (IOException e) {
    	      e.printStackTrace();
    	}
    	// Return the final array list 
		return dat;
	}
	
	/**
	 * This method compares the values contained in the input ArrayList 'dat' and the results 
	 * provided by the AtkBoo_2006_AttenRel.
	 *  
	 * @return 
	 */
	private static void CheckGMPE1(AttenuationRelationship imr,ArrayList<Double[]> dat) {
		double rrup = 0.0;
		double mag = 5.5;
		double per = 0.0;
		double sdrp;
		double vs30;
		double gmOpenSHA, gmAtkBoo;
		double dff = -1e10;
		double dst = -1;; 
		
		// Calculate values
		//System.out.printf(" rrup       m   log10(gm)   gm      Table\n");
		for (int i=0; i<dat.size(); i++){
			
			// Read parameters
			per = Math.round(1/dat.get(i)[0]*100.0)/100.0;
			mag  = dat.get(i)[2];
			rrup = dat.get(i)[4];
			vs30 = dat.get(i)[5];
			sdrp = dat.get(i)[6];
			
			// Set IMR parameters
			imr.getParameter(PeriodParam.NAME).setValue(per);
			imr.setIntensityMeasure(PGA_Param.NAME);
			if (per > 0.0){
				imr.setIntensityMeasure(SA_Param.NAME);
			} 
			//((WarningDoubleParameter)imr.getParameter(PeriodParam.NAME)).setValueIgnoreWarning(per);
			((WarningDoubleParameter)imr.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mag));
			((WarningDoublePropagationEffectParameter)imr.getParameter(DistanceRupParameter.NAME)).
				setValueIgnoreWarning(new Double(rrup));
			((WarningDoubleParameter)imr.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(vs30);
			((WarningDoubleParameter)imr.getParameter(StressDropParam.NAME)).setValueIgnoreWarning(sdrp);
			
			// Compute values
			gmOpenSHA = imr.getMean(); // Ln GM
			gmAtkBoo  = dat.get(i)[10]; // mean y
			
			// Compute the absolute difference 
			double dffprc = Math.abs(Math.exp(gmOpenSHA)-gmAtkBoo)/Math.exp(gmOpenSHA)*100;

			// HEADER
			double tmp = (double) i;
			double thr = 18.0;
			if (Math.abs(Math.round(tmp/thr)-tmp/thr) < 1e-5) 
				System.out.println("    per    rRup   mag    vs30   sDrop    OpenSHA  Boore    %dff");
			
			// Print comparison
			String lab = " ";
			if (dffprc > 1.0) lab = "+";
			System.out.printf("-- %5.2f %8.2f %5.2f %8.2f %.2f  %8.5f %8.5f %5.2f%1s \n",
					per,rrup,mag,vs30,sdrp,Math.exp(gmOpenSHA),gmAtkBoo,dffprc,lab);
		}
	}
	
	/**
	 * This reads the verification tables received on 2010.02.15. These files are in the repository
	 * directory named 'verification_Tables_AtkBoo_2006'. The suffix used to identify these files
	 * is 'ab06_output_for_comparison_*'
	 * 
	 * @param flepath
	 * @return
	 */
	public static ArrayList<Double[]> ReadTable1(String flepath){
		ArrayList<Double[]> dat = new ArrayList<Double[]>();
		String currentLine, line;
		String[] strArr;
		int cnt = 0;
		
		// Try to read 'flepath'
		try {
			// Open buffer
	    	BufferedReader input =  new BufferedReader(new FileReader(flepath));	
    		try {
    			// Read lines
    			while ((currentLine = input.readLine()) != null) {
    				cnt++;
    				// Skip the first three header lines
    				if (cnt>3) {
    					// Split the string after cleaning
    					line = currentLine.trim(); strArr = line.split("\\s+");
    					Double[] lineDat = new Double[strArr.length];
    					for (int i = 0; i < strArr.length; i++){
    						lineDat[i] = Double.valueOf(strArr[i]).doubleValue();
    					}
    					dat.add(lineDat);
    				}
    			}
    		} finally {
		    	input.close();
	    	}
		} catch (FileNotFoundException e) {
    	      e.printStackTrace();
    	} catch (IOException e) {
    	      e.printStackTrace();
    	}
    	// Return the final array list 
		return dat;
	}
	
	/**
	 * This method compares the values contained in the input ArrayList 'dat' and the results 
	 * provided by the AtkBoo_2006_AttenRel.
	 *  
	 * @return 
	 */
	private static void CheckGMPE(AttenuationRelationship imr,ArrayList<Double[]> dat) {
		double rrup = 0.0;
		double mag = 5.5;
		double gmOpenSHA, gmAtkBoo;
		double ln2log = 0.434294481903252;
		double dff = -1e10;
		double dst = -1;; 
		
		// Checking values for magnitude = 5.5
		// Set VS30
		// Set magnitude
		((WarningDoubleParameter)imr.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mag));
		// Calculate values
		System.out.printf(" rrup       m   log10(gm)   gm      Table\n");
		for (int i=0; i<dat.size(); i++){
			rrup = gmAtkBoo = dat.get(i)[1]; 
			// Set distance
			((WarningDoublePropagationEffectParameter)imr.getParameter(DistanceRupParameter.NAME)).setValueIgnoreWarning(new Double(rrup));

			gmOpenSHA = imr.getMean(); // Ln GM
			//gmOpenSHA = imr.getMean()*Math.log10(Math.E);
			//gmOpenSHA = Math.exp(gmOpenSHA);
			
			gmAtkBoo  = dat.get(i)[2];
			
			// Info
			System.out.printf("%7.2f %7.2f %8.3f %8.3f %8.3f \n",rrup,mag,gmOpenSHA*ln2log,
					Math.exp(gmOpenSHA),gmAtkBoo);
			
			// Save info
			double tmp = Math.abs(Math.exp(gmOpenSHA)-gmAtkBoo)/Math.exp(gmOpenSHA)*100.0;
			if (tmp>dff){
				dff = tmp; 
				dst = rrup;
			}
		}
		
		System.out.printf("max dff: %7.4f  dst: %6.2f\n",dff,dst);
	}
	
	/**
	 * 
	 * @param imr
	 * @param dst
	 */
	public static void ComputeSpectrum(ScalarIntensityMeasureRelationshipAPI imr, double dst){
		ArrayList<Double> per = getPeriods(imr);
		for (int i = 0; i < per.size(); i++){	 
	        double tmp = per.get(i);
	        if (tmp == 0.0){
	        	imr.setIntensityMeasure(PGA_Param.NAME);
	        } else {
	        	imr.setIntensityMeasure(SA_Param.NAME);
	        	imr.getParameter(PeriodParam.NAME).setValue(tmp);
	        }
	        double gm = imr.getMean(); 
	        System.out.printf("%7.3f %7.3f\n",per.get(i), Math.exp(gm));
		}	
	}
	
	/**
	 * 
	 * @param imr
	 * @return
	 */
	private static ArrayList<Double> getPeriods(ScalarIntensityMeasureRelationshipAPI imr) {
		// Get the list of periods available for the selected IMR
		ArrayList<Double> per = new ArrayList<Double>();
		ListIterator<ParameterAPI<?>> it = imr.getSupportedIntensityMeasuresIterator();
	    while(it.hasNext()){
	    	DependentParameterAPI tempParam = (DependentParameterAPI)it.next();
	    	if (tempParam.getName().equalsIgnoreCase(SA_Param.NAME)){
	    		ListIterator it1 = tempParam.getIndependentParametersIterator();
	    		while(it1.hasNext()){
	    			ParameterAPI independentParam = (ParameterAPI)it1.next();
	    			if (independentParam.getName().equalsIgnoreCase(PeriodParam.NAME)){
	    				ArrayList<Double> saPeriodVector = ((DoubleDiscreteParameter)independentParam).getAllowedDoubles();
	    				
	    				for (int h=0; h<saPeriodVector.size(); h++){
	    					if (h == 0 && saPeriodVector.get(h)>0.0){
	    						per.add(0.0);
	    					}
	    					per.add(saPeriodVector.get(h));
	    				}
	    				
	    			}
	    		}
	    	}
	    }
	    return per;
	}

	
}
