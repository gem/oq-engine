/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.analysis;

import java.io.FileOutputStream;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UnsegmentedSource;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 *  This creates an excel sheet with B-Faults and various values associated with them.
 *  The sheet was used as a part of Supplemntal Data for UCERF2 report 
 *  After excel sheet is made, some things need to be done explicity like sorting by 
 *  name and then writing Ids of connected faults.
 *  
 * @author vipingupta
 *
 */
public class MakeB_FaultsTable {
	private final static String CA_B_FILENAME = "B-Faults.xls";
	private final static String NON_CA_B_FILENAME = "Non-CA_B-Faults.xls";
	private final static DecimalFormat SLIP_RATE_FORMAT = new DecimalFormat("0.#####");
	private final static DecimalFormat AREA_LENGTH_FORMAT = new DecimalFormat("0.#");
	private final static DecimalFormat MOMENT_FORMAT = new DecimalFormat("0.000E0");
	private final static DecimalFormat MAG_FORMAT = new DecimalFormat("0.00");
	private final static DecimalFormat RATE_FORMAT = new DecimalFormat("0.00000");
	private final static DecimalFormat ASEISMSIC_FORMAT = new DecimalFormat("0.00");
	// bFaults name and row Id mapping
	private HashMap<String, Integer> nameRowMapping;
	private HashMap<String, String> nameFaultModelMapping;

	private HSSFWorkbook workbook  = new HSSFWorkbook();
	private HSSFSheet sheet;
	private UCERF2 ucerf2 = new UCERF2();
	int rowIndex;
	public MakeB_FaultsTable() {

		ucerf2 = new UCERF2();


		workbook  = new HSSFWorkbook();

		// Make a sheet excluding connecting B-Faults
		makeCA_B_FaultsNewSheet("B-Faults");
		rowIndex=2;
		makeData(false, "D2.1"); // do for Deformation Model 2.1
		makeData(false, "D2.4"); // do for Deformation Model 2.4


		Iterator<String> bFaultNamesIt = nameRowMapping.keySet().iterator();
		while(bFaultNamesIt.hasNext()) {
			String faultName = bFaultNamesIt.next();
			int rId = nameRowMapping.get(faultName);
			sheet.getRow(rId).createCell((short)13).setCellValue(nameFaultModelMapping.get(faultName));
		}

		rowIndex=2;
		// Make a sheet for only Connected B-Faults
		makeCA_B_FaultsNewSheet("Connected B-Faults");
		makeData(true, "D2.1");
		makeData(true, "D2.4");
		bFaultNamesIt = nameRowMapping.keySet().iterator();
		while(bFaultNamesIt.hasNext()) {
			String faultName = bFaultNamesIt.next();
			int rId = nameRowMapping.get(faultName);
			sheet.getRow(rId).createCell((short)13).setCellValue(nameFaultModelMapping.get(faultName));
		}
//		write  excel sheet
		try {
			FileOutputStream fileOut = new FileOutputStream(this.CA_B_FILENAME);
			workbook.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}

		workbook  = new HSSFWorkbook();
		rowIndex=2;
		makeNonCA_B_FaultsNewSheet("Non-CA B-Faults");
		makeNonCAB_FaultsData();

//		write  excel sheet
		try {
			FileOutputStream fileOut = new FileOutputStream(this.NON_CA_B_FILENAME);
			workbook.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}

	}

	/**
	 * Make a sheet for Non-California B-Faults
	 * 
	 * @param sheetName
	 */
	private void makeNonCA_B_FaultsNewSheet(String sheetName) {
		sheet = workbook.createSheet(sheetName);
		HSSFRow row = sheet.createRow(0);
		row.createCell((short)2).setCellValue("Ellsworth B");
		row.createCell((short)4).setCellValue("Hans & Bakun 2002");
		row  = sheet.createRow(1);
		row.createCell((short)0).setCellValue("Index");
		row.createCell((short)1).setCellValue("Name");
		row.createCell((short)2).setCellValue("Mag");
		row.createCell((short)3).setCellValue("Rate");
		row.createCell((short)4).setCellValue("Mag");
		row.createCell((short)5).setCellValue("Rate");
		row.createCell((short)6).setCellValue("Prob (Mag>=6.7)");
		row.createCell((short)7).setCellValue("Empirical Correction");
		row.createCell((short)8).setCellValue("Slip Rate (mm/yr)");
		row.createCell((short)9).setCellValue("Area (sq-km)");
		row.createCell((short)10).setCellValue("Length (km)");
		row.createCell((short)11).setCellValue("Moment Rate (Newton-meters/yr)");
		row.createCell((short)12).setCellValue("Fault Model");
		nameRowMapping = new  HashMap<String, Integer>();
		nameFaultModelMapping = new  HashMap<String, String>();

	}

	private void makeCA_B_FaultsNewSheet(String sheetName) {
		sheet = workbook.createSheet(sheetName);
		HSSFRow row = sheet.createRow(0);
		row.createCell((short)2).setCellValue("Ellsworth B");
		row.createCell((short)3).setCellValue("Hans & Bakun 2002");
		row  = sheet.createRow(1);
		row.createCell((short)0).setCellValue("Index");
		row.createCell((short)1).setCellValue("Name");
		row.createCell((short)2).setCellValue("Mag");
		row.createCell((short)3).setCellValue("Mag");
		row.createCell((short)4).setCellValue("Poiss Prob  (Mag>=6.7)");
		row.createCell((short)5).setCellValue("Mean Prob (Mag>=6.7)");
		row.createCell((short)6).setCellValue("Min Prob (Mag>=6.7)");
		row.createCell((short)7).setCellValue("Max Prob (Mag>=6.7)");
		row.createCell((short)8).setCellValue("Empirical Correction");
		row.createCell((short)9).setCellValue("Slip Rate (mm/yr)");
		row.createCell((short)10).setCellValue("Area (sq-km)");
		row.createCell((short)11).setCellValue("Length (km)");
		row.createCell((short)12).setCellValue("Moment Rate (Newton-meters/yr)");
		row.createCell((short)13).setCellValue("Fault Model");
		nameRowMapping = new  HashMap<String, Integer>();
		nameFaultModelMapping = new  HashMap<String, String>();

	}

	/**
	 * Write the excel sheet for Non-CA  B-Faults
	 *
	 */
	private void makeNonCAB_FaultsData() {

		HashMap<String, Double> sourceRateMapping = new HashMap<String, Double>();
		HashMap<String, Double> sourceProb6_7Mapping = new HashMap<String, Double>();
		HashMap<String, Double> sourceEmpMapping = new HashMap<String, Double>();
		HashMap<String, Double> sourceLengthMapping = new HashMap<String, Double>();
		HashMap<String, Double> sourceAreaMapping = new HashMap<String, Double>();
		HashMap<String, Double> sourceMoRateMapping = new HashMap<String, Double>();
		// Poisson
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);
		ucerf2.updateForecast();
		ArrayList<ProbEqkSource> nonCA_Sources_Poiss = ucerf2.getNonCA_B_FaultSources();
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_EMPIRICAL);
		ucerf2.updateForecast();
		ArrayList<ProbEqkSource> nonCA_Sources_Emp = ucerf2.getNonCA_B_FaultSources();

		double duration = ucerf2.getTimeSpan().getDuration();
		HSSFRow row;
		HashMap<String, Double> sourceMagMapping = new HashMap<String, Double>();
		String fileName = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/data/NearCA_NSHMP/NonCA_Faults.txt";
		
		// The file reading has been copied from NonCA_FaultsFetcher class
		
 		try {
			//FileWriter fw = new FileWriter("NonCA_Sources.txt");
			//fw.write("Total Yearly Rate\tTotal Moment Rate\tSource Name\n");
			ArrayList<String> fileLines = FileUtils.loadJarFile(fileName);
			int numLines = fileLines.size();
			int rakeId, srcTypeId;
			double mag=0, dip, downDipWidth, upperSeisDepth, lowerSeisDepth, latitude, longitude, rake;
			FaultTrace faultTrace;
			String faultName;
			for(int i=0; i<numLines; ) {
				String line = fileLines.get(i++);
				StringTokenizer tokenizer = new StringTokenizer(line);
				srcTypeId = Integer.parseInt(tokenizer.nextToken().trim());
				rakeId = Integer.parseInt(tokenizer.nextToken().trim());
				int numMags = Integer.parseInt(tokenizer.nextToken().trim());
				tokenizer.nextToken();  // we were told this element is useless
				faultName = "";
				while(tokenizer.hasMoreTokens()) faultName+=tokenizer.nextToken()+" ";
				// mag, rate & wt
				line = fileLines.get(i++);
				tokenizer = new StringTokenizer(line);
				double moRate;
				if(srcTypeId==1) { // Char case
					mag = Double.parseDouble(tokenizer.nextToken().trim());
					double rate = Double.parseDouble(tokenizer.nextToken().trim());
					moRate = rate*MomentMagCalc.getMoment(mag);
					double wt = Double.parseDouble(tokenizer.nextToken().trim());
					double wt2 = 1;
					if(mag > 6.5) wt2 = 0.666;
					moRate *= wt*wt2;
				}
				else if (srcTypeId==2) { // GR Case
					double aVal=Double.parseDouble(tokenizer.nextToken().trim());
					double bVal=Double.parseDouble(tokenizer.nextToken().trim());
					double magLower=Double.parseDouble(tokenizer.nextToken().trim());
					double magUpper=Double.parseDouble(tokenizer.nextToken().trim());
					double deltaMag=Double.parseDouble(tokenizer.nextToken());
					mag=magUpper;
					//System.out.println(faultName+","+magLower+","+magUpper);
					if(magUpper!=magLower) {
						magLower += deltaMag/2.0;
						magUpper -= deltaMag/2.0;
					}
					else {
						magLower=Math.round( (float)((magUpper-UCERF2.MIN_MAG)/deltaMag)) * deltaMag + UCERF2.MIN_MAG;
						magUpper= magLower;
					}
					numMags = Math.round( (float)((magUpper-magLower)/deltaMag + 1.0) );
					//if(numMags==0) System.out.println(faultName+","+magLower+","+magUpper);
					moRate = Frankel02_AdjustableEqkRupForecast.getMomentRate(magLower, numMags, deltaMag, aVal, bVal);
					double wt = Double.parseDouble(tokenizer.nextToken().trim());
					double wt2 = 0.334;
					moRate *= wt*wt2;
				}	

				else throw new RuntimeException("Src type not supported");
				if(sourceMagMapping.containsKey(faultName)) {
					double mag1 = sourceMagMapping.get(faultName);
					if(Math.abs(mag1-mag)>0.001) throw new RuntimeException("Wrong mags for source "+faultName+":"+mag1+","+mag);
					double newMoRate = sourceMoRateMapping.get(faultName) + moRate;
					sourceMoRateMapping.put(faultName, newMoRate);
				} else {
					sourceMagMapping.put(faultName, mag);
					sourceMoRateMapping.put(faultName, moRate);
					double rate=0;
					double rate6_7=0, emp=0, num=0;
					for(int srcId=0; srcId<nonCA_Sources_Poiss.size(); ++srcId) {
						ProbEqkSource source_pois = (ProbEqkSource)nonCA_Sources_Poiss.get(srcId);
						ProbEqkSource source_emp = (ProbEqkSource)nonCA_Sources_Emp.get(srcId);
						if(source_pois.getName().equalsIgnoreCase(faultName+" GR") ||
								source_pois.getName().equalsIgnoreCase(faultName+" Char")) {
							double prob = source_pois.computeTotalProb();
							rate+= -Math.log(1-prob)/duration;
							rate6_7+= -Math.log(1-source_pois.computeTotalProbAbove(6.7))/duration;
							emp+=source_emp.computeTotalProb()/prob;
							++num;
						}

					}
					sourceProb6_7Mapping.put(faultName, 1-Math.exp(-rate6_7*duration));
					sourceRateMapping.put(faultName, rate);
					sourceEmpMapping.put(faultName, emp/num);
				}

				// dip, surface width, upper seis depth, surface length
				// dip, surface width, upper seis depth, surface length
				line = fileLines.get(i++);
				tokenizer = new StringTokenizer(line);
				dip = Double.parseDouble(tokenizer.nextToken().trim());
				downDipWidth = Double.parseDouble(tokenizer.nextToken().trim());
				upperSeisDepth = Double.parseDouble(tokenizer.nextToken().trim());
				lowerSeisDepth = upperSeisDepth + downDipWidth*Math.sin((Math.toRadians(Math.abs(dip))));

				//fault trace
				line = fileLines.get(i++);
				int numLocations = Integer.parseInt(line.trim());
				faultTrace = new FaultTrace(faultName);
				for(int locIndex=0; locIndex<numLocations; ++locIndex) {
					line = fileLines.get(i++);
					tokenizer = new StringTokenizer(line);
					latitude = Double.parseDouble(tokenizer.nextToken());
					longitude =Double.parseDouble(tokenizer.nextToken());
					faultTrace.add(new Location(latitude, longitude));
				}		
				sourceLengthMapping.put(faultName, faultTrace.getTraceLength());
				sourceAreaMapping.put(faultName, faultTrace.getTraceLength()*downDipWidth);
			}
		}catch (Exception e) {
			e.printStackTrace();
		}	

		Iterator<String> it = sourceMagMapping.keySet().iterator();
		while(it.hasNext()) {
			String faultName = it.next();
			double mag = sourceMagMapping.get(faultName);
			double rate = sourceRateMapping.get(faultName);
			row  = sheet.createRow(rowIndex);
			row.createCell((short)1).setCellValue(faultName);
			row.createCell((short)2).setCellValue(MAG_FORMAT.format(mag));
			row.createCell((short)3).setCellValue((float)rate);
			row.createCell((short)4).setCellValue(MAG_FORMAT.format(mag));
			row.createCell((short)5).setCellValue((float)rate);
			row.createCell((short)6).setCellValue(sourceProb6_7Mapping.get(faultName));
			row.createCell((short)7).setCellValue(sourceEmpMapping.get(faultName));
			row.createCell((short)9).setCellValue(AREA_LENGTH_FORMAT.format(sourceAreaMapping.get(faultName)));
			row.createCell((short)10).setCellValue(AREA_LENGTH_FORMAT.format(sourceLengthMapping.get(faultName)));
			row.createCell((short)11).setCellValue(MOMENT_FORMAT.format(sourceMoRateMapping.get(faultName)));

			rowIndex++;
		}

	}

	/**
	 * Write to the excel sheet for B-Faults. This method loops overall logic tree branches for the
	 * given deformation model and writes B-Fault associated data such as mean Prob, max Prob,
	 * min Prob, empirical val, area, length, slip rate, moment rate.
	 * 
	 * @param connectMoreB_Faults Whether to connect more B-Faults
	 * @param defModelName Deformation model for which data is generated
	 */
	private void makeData(boolean connectMoreB_Faults, String defModelName) {

		ucerf2.getParameter(UCERF2.CONNECT_B_FAULTS_PARAM_NAME).setValue(new Boolean(connectMoreB_Faults));
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue(defModelName);

		// bVal = 0.8
		ucerf2.getParameter(UCERF2.B_FAULTS_B_VAL_PARAM_NAME).setValue(0.8);

		// Poisson - bVal=0.8
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(Ellsworth_B_WG02_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesEllB_Poiss_8 = ucerf2.get_B_FaultSources();

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesHB_Poiss_8 = ucerf2.get_B_FaultSources();

		// Empirical - bVal=0.8
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_EMPIRICAL);

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(Ellsworth_B_WG02_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesEllB_Emp_8 = ucerf2.get_B_FaultSources();

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesHB_Emp_8 = ucerf2.get_B_FaultSources();


		//		 bVal = 0.0
		ucerf2.getParameter(UCERF2.B_FAULTS_B_VAL_PARAM_NAME).setValue(0.0);

		// Poisson - bVal=0.0
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(Ellsworth_B_WG02_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesEllB_Poiss_0 = ucerf2.get_B_FaultSources();

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesHB_Poiss_0 = ucerf2.get_B_FaultSources();

		// Empirical - bVal=0.0
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_EMPIRICAL);

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(Ellsworth_B_WG02_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesEllB_Emp_0 = ucerf2.get_B_FaultSources();

		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		ArrayList<UnsegmentedSource> bFaultSourcesHB_Emp_0 = ucerf2.get_B_FaultSources();


		HSSFRow row;
		String faultModel = null;

		if(defModelName.equalsIgnoreCase("D2.4")) faultModel="F2.2";
		else if(defModelName.equalsIgnoreCase("D2.1")) faultModel="F2.1";
		else throw new RuntimeException("Unsupported deformation model");
		double MAG = 6.7;
		for(int i=0; i<bFaultSourcesEllB_Poiss_8.size(); ++i) {

			UnsegmentedSource sourceEllB_Poiss_8 = bFaultSourcesEllB_Poiss_8.get(i);
			UnsegmentedSource sourceHB_Poiss_8 = bFaultSourcesHB_Poiss_8.get(i);
			UnsegmentedSource sourceEllB_Emp_8 = bFaultSourcesEllB_Emp_8.get(i);
			UnsegmentedSource sourceHB_Emp_8 = bFaultSourcesHB_Emp_8.get(i);

			UnsegmentedSource sourceEllB_Poiss_0 = bFaultSourcesEllB_Poiss_0.get(i);
			UnsegmentedSource sourceHB_Poiss_0 = bFaultSourcesHB_Poiss_0.get(i);
			UnsegmentedSource sourceEllB_Emp_0 = bFaultSourcesEllB_Emp_0.get(i);
			UnsegmentedSource sourceHB_Emp_0 = bFaultSourcesHB_Emp_0.get(i);

			FaultSegmentData faultSegmentData = sourceEllB_Poiss_8.getFaultSegmentData();
			row  = sheet.createRow(rowIndex);
			String bFaultName = faultSegmentData.getFaultName();
			if(connectMoreB_Faults && bFaultName.indexOf("Connected")==-1) continue;
			if(!connectMoreB_Faults && bFaultName.indexOf("Connected")!=-1) continue;
			if(nameRowMapping.containsKey(bFaultName)) {
				String faultModelName = nameFaultModelMapping.get(bFaultName);
				faultModelName+=",F2.2";
				nameFaultModelMapping.put(bFaultName, faultModelName);
				continue;
			}
			nameRowMapping.put(bFaultName, rowIndex); // bFault and rowId mapping
			nameFaultModelMapping.put(bFaultName, faultModel); // bFault and fault model mapping

			double probEllB_Poiss_8, probHB_Poiss_8, probEllB_Emp_8, probHB_Emp_8;
			double probEllB_Poiss_0, probHB_Poiss_0, probEllB_Emp_0, probHB_Emp_0;
			double minProb = Double.MAX_VALUE, maxProb = -1.0;

			probEllB_Poiss_8 = sourceEllB_Poiss_8.computeTotalProbAbove(MAG);
			if(probEllB_Poiss_8<minProb) minProb = probEllB_Poiss_8;
			if(probEllB_Poiss_8>maxProb) maxProb = probEllB_Poiss_8;

			probHB_Poiss_8 = sourceHB_Poiss_8.computeTotalProbAbove(MAG);
			if(probHB_Poiss_8<minProb) minProb = probHB_Poiss_8;
			if(probHB_Poiss_8>maxProb) maxProb = probHB_Poiss_8;

			probEllB_Emp_8 = sourceEllB_Emp_8.computeTotalProbAbove(MAG);
			if(probEllB_Emp_8<minProb) minProb = probEllB_Emp_8;
			if(probEllB_Emp_8>maxProb) maxProb = probEllB_Emp_8;

			probHB_Emp_8 = sourceHB_Emp_8.computeTotalProbAbove(MAG);
			if(probHB_Emp_8<minProb) minProb = probHB_Emp_8;
			if(probHB_Emp_8>maxProb) maxProb = probHB_Emp_8;

			probEllB_Poiss_0 = sourceEllB_Poiss_0.computeTotalProbAbove(MAG);
			if(probEllB_Poiss_0<minProb) minProb = probEllB_Poiss_0;
			if(probEllB_Poiss_0>maxProb) maxProb = probEllB_Poiss_0;

			probHB_Poiss_0 = sourceHB_Poiss_0.computeTotalProbAbove(MAG);
			if(probHB_Poiss_0<minProb) minProb = probHB_Poiss_0;
			if(probHB_Poiss_0>maxProb) maxProb = probHB_Poiss_0;

			probEllB_Emp_0 = sourceEllB_Emp_0.computeTotalProbAbove(MAG);
			if(probEllB_Emp_0<minProb) minProb = probEllB_Emp_0;
			if(probEllB_Emp_0>maxProb) maxProb = probEllB_Emp_0;

			probHB_Emp_0 = sourceHB_Emp_0.computeTotalProbAbove(MAG);
			if(probHB_Emp_0<minProb) minProb = probHB_Emp_0;
			if(probHB_Emp_0>maxProb) maxProb = probHB_Emp_0;

			double meanPoissonProb = (probEllB_Poiss_8+probHB_Poiss_8+probEllB_Poiss_0+probHB_Poiss_0)/4;
			double meanProb = (0.7)*(probEllB_Poiss_8+probHB_Poiss_8+probEllB_Poiss_0+probHB_Poiss_0)/4+
				(0.3)*(probEllB_Emp_8+probHB_Emp_8+probEllB_Emp_0+probHB_Emp_0)/4;

			//row.createCell((short)0).setCellValue(rowIndex-1);
			row.createCell((short)1).setCellValue(bFaultName);
			row.createCell((short)2).setCellValue(MAG_FORMAT.format(sourceEllB_Poiss_8.getSourceMag()));
			row.createCell((short)3).setCellValue(MAG_FORMAT.format(sourceHB_Poiss_8.getSourceMag()));
			row.createCell((short)4).setCellValue((float)meanPoissonProb);
			row.createCell((short)5).setCellValue((float)meanProb);
			row.createCell((short)6).setCellValue((float)minProb);
			row.createCell((short)7).setCellValue((float)maxProb);
			row.createCell((short)8).setCellValue((float)(meanProb/meanPoissonProb));
			row.createCell((short)9).setCellValue(SLIP_RATE_FORMAT.format(faultSegmentData.getTotalAveSlipRate()*1e3));
			row.createCell((short)10).setCellValue(AREA_LENGTH_FORMAT.format(faultSegmentData.getTotalArea()/1e6));
			row.createCell((short)11).setCellValue(AREA_LENGTH_FORMAT.format(faultSegmentData.getTotalLength()/1e3));
			row.createCell((short)12).setCellValue(MOMENT_FORMAT.format(sourceEllB_Poiss_8.getMomentRate()));
			++rowIndex;
		}
	}

	public static void main(String []args) {
		new MakeB_FaultsTable();
	}

}
