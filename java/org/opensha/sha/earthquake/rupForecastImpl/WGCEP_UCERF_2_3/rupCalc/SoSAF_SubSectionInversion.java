/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.rupCalc;

import java.io.FileWriter;
import java.util.ArrayList;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.calc.nnls.NNLSWrapper;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelPrefDataDB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data.SegRateConstraint;
import org.opensha.sha.gui.infoTools.GraphiWindowAPI_Impl;
import org.opensha.sha.magdist.SummedMagFreqDist;

/**
 * This class finds the subsections for S. San Andreas fault 
 * 
 * @author vipingupta
 *
 */
public class SoSAF_SubSectionInversion {
	private final static String SEG_RATE_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/Appendix_C_Table7_091807.xls";

	private boolean D = true;
	private final static int MAX_SUBSECTION_LEN = 10;
	private DeformationModelPrefDataDB_DAO deformationModelPrefDB_DAO = new DeformationModelPrefDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private ArrayList<FaultSectionPrefData> subSectionList;
	
	private int num_seg, num_rup;
	
	ArrayList<SegRateConstraint> segRateConstraints;
	
	// a-priori rate constraints
	int[] aPriori_rupIndex;
	double[] aPriori_rate, aPriori_wt;
	
	private static boolean MATLAB_TEST = false;
	double[][] C_wted, C;
	double[] d, d_wted, data_wt, full_wt, d_pred;  // the data vector
	
	private double minRates[]; // the minimum rate constraint for each rupture
	private boolean wtedInversion;	// weight the inversion according to slip rate and segment rate uncertainties
	private double relativeSegRateWt, relative_aPrioriRupWt, relative_smoothnessWt;
	
	private int  firstRowSegSlipRateData=-1,firstRowSegEventRateData=-1, firstRowAprioriData=-1, firstRowSmoothnessData=-1;
	private int  lastRowSegSlipRateData=-1,lastRowSegEventRateData=-1, lastRowAprioriData=-1, lastRowSmoothnessData=-1;
	private int totNumRows;


;
	
	// slip model:
	private String slipModelType;
	public final static String CHAR_SLIP_MODEL = "Characteristic (Dsr=Ds)";
	public final static String UNIFORM_SLIP_MODEL = "Uniform/Boxcar (Dsr=Dr)";
	public final static String WG02_SLIP_MODEL = "WGCEP-2002 model (Dsr prop to Vs)";
	public final static String TAPERED_SLIP_MODEL = "Tapered Ends ([Sin(x)]^0.5)";
	
	private static EvenlyDiscretizedFunc taperedSlipPDF, taperedSlipCDF;
	
	SummedMagFreqDist magFreqDist;
	
	private int[][] rupInSeg;
	private double[][] segSlipInRup;
	
	private double[] finalSegEventRate, finalSegSlipRate;
	private double[] segSlipRateResids, segEventRateResids;
	
	private String[] rupNameShort;
	private double[] rupArea, rupMeanMag, rupMeanMo, rupMoRate, totRupRate, segArea, segSlipRate, segSlipRateStdDev, segMoRate;
	double[] rupRateSolution; // these are the rates from the inversion (not total rate of MFD)
	
	// the following is the total moment-rate reduction, including that which goes to the  
	// background, sfterslip, events smaller than the min mag here, and aftershocks and foreshocks.
	private double moRateReduction;  
	
	private MagAreaRelationship magAreaRel;
	
	// NNLS inversion solver - static to save time and memory
	private static NNLSWrapper nnls = new NNLSWrapper();

	
	public SoSAF_SubSectionInversion() {
		
		
		// chop the SSAF into many sub-sections
		computeAllSubsections();
		
		// get the RupInSeg Matrix for the given number of segments
		num_seg = subSectionList.size();
		rupInSeg = getRupInSegMatrix(num_seg);
		num_rup = num_seg*(num_seg+1)/2;
		if(D) System.out.println("num_seg="+num_seg+"; num_rup="+num_rup);
		
		// make short rupture names
		rupNameShort = new String[num_rup];
		for(int rup=0; rup<num_rup; rup++){
			boolean isFirst = true;
			for(int seg=0; seg < num_seg; seg++) {
				if(rupInSeg[seg][rup]==1) { // if this rupture is included in this segment
					if(isFirst) { // append the section name to rupture name
						rupNameShort[rup] = ""+(seg);
						isFirst = false;
					} else {
						rupNameShort[rup] += "+"+(seg);
					}
				}
			}
//			if(D) System.out.println(rup+"\t"+rupNameShort[rup]);
		}

		// compute rupture areas
		computeInitialStuff();
		
		// create the segRateConstraints
		computeSegRateConstraints();
		
		// set the a-priori rup rates & wts
		setAprioriRateData();
	}
	
	
	/**
	 * Write Short Rup names to a file
	 * 
	 * @param fileName
	 */
	public void writeRupNamesToFile(String fileName) {
		try{
			FileWriter fw = new FileWriter("org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/rupCalc/"+fileName);
			fw.write("rup_index\trupNameShort\n");
			for(int i=0; i<rupNameShort.length; ++i)
				fw.write(i+"\t"+rupNameShort[i]+"\n");
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	
	public void doInversion(String slipModelType, MagAreaRelationship magAreaRel, double relativeSegRateWt, 
			double relative_aPrioriRupWt, double relative_smoothnessWt, boolean wtedInversion) {
		
		this.slipModelType = slipModelType;
		this.magAreaRel = magAreaRel;
		this.relativeSegRateWt = relativeSegRateWt;
		this.relative_aPrioriRupWt = relative_aPrioriRupWt;
		this.wtedInversion = wtedInversion;
		this.relative_smoothnessWt = relative_smoothnessWt;

		// hard coded moment-rate reduction
		moRateReduction=0;
				
		// compute rupture mean mags
		if(slipModelType.equals(CHAR_SLIP_MODEL))
			// getRupMeanMagsAssumingCharSlip();
			throw new RuntimeException(CHAR_SLIP_MODEL+" is not yet supported");
		else {
			// compute from mag-area relationship
			rupMeanMag = new double[num_rup];
			rupMeanMo = new double[num_rup];
			for(int rup=0; rup <num_rup; rup++) {
				rupMeanMag[rup] = magAreaRel.getMedianMag(rupArea[rup]/1e6);
				rupMeanMo[rup] = MomentMagCalc.getMoment(rupMeanMag[rup]);   // increased if magSigma >0
			}
		}

		// compute matrix of Dsr (slip on each segment in each rupture)
		computeSegSlipInRupMatrix();
					
		// get the number of segment rate constraints
		int numRateConstraints = segRateConstraints.size();
		
		// get the number of a-priori rate constraints
		int num_aPriori_constraints = aPriori_rupIndex.length;
		
		// set the minimum rupture rate constraints
		setMinRates();

		// SET NUMBER OF ROWS AND IMPORTANT INDICES
		
		// segment slip-rates always used (for now)
		firstRowSegSlipRateData = 0;
		totNumRows = num_seg;
		lastRowSegSlipRateData = totNumRows-1;
		
		// add segment rate constrains if needed
		if(relativeSegRateWt > 0.0) {
			firstRowSegEventRateData = totNumRows;
			totNumRows += numRateConstraints;
			lastRowSegEventRateData = totNumRows-1;
		}
		
		// add a-priori rate constrains if needed
		if(relative_aPrioriRupWt > 0.0) {
			firstRowAprioriData  = totNumRows;
			totNumRows += num_aPriori_constraints;
			lastRowAprioriData = totNumRows-1;
		}
		
		// add number of smoothness constraints
		if(relative_smoothnessWt > 0) {
			firstRowSmoothnessData=totNumRows;
			totNumRows += num_rup-num_seg;
			lastRowSmoothnessData = totNumRows-1;
		}
			
		C = new double[totNumRows][num_rup];
		d = new double[totNumRows];  // data vector
		C_wted = new double[totNumRows][num_rup]; // wted version
		d_wted = new double[totNumRows];  // wted data vector

		data_wt = new double[totNumRows];  // data weights
		full_wt = new double[totNumRows];  // data weights
		d_pred = new double[totNumRows];  // predicted data vector
		
		// initialize wts to 1.0
		for(int i=0;i<data_wt.length;i++)  data_wt[i]=1.0;
			
		// CREATE THE MODEL AND DATA MATRICES
		// first fill in the slip-rate constraints & wts
		for(int row = firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row ++) {
			d_wted[row] = segSlipRate[row]*(1-moRateReduction);
			if(wtedInversion)
				data_wt[row] = 1/((1-moRateReduction)*segSlipRateStdDev[row]);
			for(int col=0; col<num_rup; col++)
				C_wted[row][col] = segSlipInRup[row][col];
		}
		// now fill in the segment event rate constraints if requested
		if(relativeSegRateWt > 0.0) {
			SegRateConstraint constraint;
			for(int i = 0; i < numRateConstraints; i ++) {
				constraint = segRateConstraints.get(i);
				int seg = constraint.getSegIndex();
				int row = i+firstRowSegEventRateData;
				d_wted[row] = constraint.getMean(); // this is the average segment rate
				if(wtedInversion)
					data_wt[row] = 1/constraint.getStdDevOfMean();
				for(int col=0; col<num_rup; col++)
					C_wted[row][col] = rupInSeg[seg][col];
			}
		}
		// now fill in the a-priori rates if needed
		if(relative_aPrioriRupWt > 0.0) {
			for(int i=0; i < num_aPriori_constraints; i++) {
				int row = i+firstRowAprioriData;
				int col = aPriori_rupIndex[i];
				d_wted[row] = aPriori_rate[i];
				if(wtedInversion)
					data_wt[row] = aPriori_wt[i];
				C_wted[row][col]=1.0;
			}
		}
		// add the smoothness constraint
		if(relative_smoothnessWt > 0.0) {
			int row = firstRowSmoothnessData;
			for(int rup=0; rup < num_rup; rup++) {
				// check to see if the last segment is used by the rupture (skip this last rupture if so)
				if(rupInSeg[num_seg-1][rup] != 1) {
					d_wted[row] = 0;
					C_wted[row][rup]=1.0;
					C_wted[row][rup+1]=-1.0;
					row += 1;
//					num_smooth_constrints += 1;
				}
			}
		}
//		System.out.println("num_smooth_constrints="+num_smooth_constrints);
		
		// save the un-wted data
		for(int row=0;row<totNumRows; row++){
			d[row] = d_wted[row];
			for(int col=0;col<num_rup; col++)
				C[row][col] = C_wted[row][col];
		}
			
		

		// CORRECT IF MINIMUM RATE CONSTRAINT DESIRED
		double[] Cmin = new double[totNumRows];  // the data vector
		// correct the data vector
		for(int row=0; row <totNumRows; row++) {
			for(int col=0; col < num_rup; col++)
				Cmin[row]+=minRates[col]*C_wted[row][col];
			d_wted[row] -= Cmin[row];
		}
		
		// APPLY WEIGHTS

		
		// segment slip rates first (no equation-set weight because others are relative)
		for(int row = firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row ++) {
			if(wtedInversion) 
				full_wt[row] = data_wt[row];
			else
				full_wt[row] = 1.0;
			d_wted[row] *= full_wt[row];
			for(int col=0; col<num_rup; col++)
				C_wted[row][col] *= full_wt[row];
		}
		// segment event rate wts
		if(relativeSegRateWt > 0.0) {
			for(int i = 0; i < numRateConstraints; i ++) {
				int row = i+firstRowSegEventRateData;
				full_wt[row] = relativeSegRateWt;
				if(wtedInversion) full_wt[row] *= data_wt[row];
				d_wted[row] *= full_wt[row]; // this is the average segment rate
				for(int col=0; col<num_rup; col++)
					C_wted[row][col] *= full_wt[row];
			}
		}
		// a-priori rate wts
		if(relative_aPrioriRupWt > 0.0) {
			for(int i=0; i < num_aPriori_constraints; i++) {
				int row = i+firstRowAprioriData;
				int col = aPriori_rupIndex[i];
				full_wt[row] = relative_aPrioriRupWt;
				if(wtedInversion) full_wt[row] *= data_wt[row];
				d_wted[row] *= full_wt[row];
				C_wted[row][col]=full_wt[row];
			}
		}
		// smoothness constraint wts
		if(relative_smoothnessWt > 0.0) {
			int row = firstRowSmoothnessData;
			for(int rup=0; rup < num_rup; rup++) {
				// check to see if the last segment is used by the rupture (skip this last rupture if so)
				if(rupInSeg[num_seg-1][rup] != 1) {
					full_wt[row] = relative_smoothnessWt;
					d_wted[row] *= full_wt[row];
					C_wted[row][rup] *= full_wt[row];
					C_wted[row][rup+1] *= full_wt[row];
					row += 1;
//					num_smooth_constrints += 1;
				}
			}
		}


		
//		for(int row=0;row<totNumRows; row++)
//			System.out.println(row+"\t"+(float)d[row]);

/*
		// manual check of matrices
			int nRow = C.length;
			int nCol = C[0].length;
			System.out.println("C = [");
			for(int i=0; i<nRow;i++) {
				for(int j=0;j<nCol;j++) 
					System.out.print(C[i][j]+"   ");
				System.out.print("\n");
			}
			System.out.println("];");
			System.out.println("d = [");
			for(int i=0; i<nRow;i++)
				System.out.println(d[i]);
			System.out.println("];");
*/

		// SOLVE THE INVERSE PROBLEM
		rupRateSolution = getNNLS_solution(C_wted, d_wted);

		// CORRECT FINAL RATES IF MINIMUM RATE CONSTRAINT APPLIED
		for(int rup=0; rup<num_rup;rup++)
			rupRateSolution[rup] += minRates[rup];
		
		// compute predicted data
		for(int row=0;row<totNumRows; row++)
			for(int col=0; col <num_rup; col++)
				d_pred[row] += rupRateSolution[col]*C[row][col];
				
		// Compute final segment slip rates and event rates
		computeFinalStuff();
		
	}
	
	
	
	
	/**
	 * Get a list of all subsections
	 * 
	 * @return
	 */
	private void computeAllSubsections() {
		/** Choose a deformation model
		 * D2.1 = 82
		 * D2.2 = 83
		 * D2.3 = 84
		 * D2.4 = 85
		 * D2.5 = 86
		 * D2.6 = 87
		 */
		int deformationModelId = 82; //
		
		/*32:San Andreas (Parkfield)
		285:San Andreas (Cholame) rev
		300:San Andreas (Carrizo) rev
		287:San Andreas (Big Bend)
		286:San Andreas (Mojave N)
		301:San Andreas (Mojave S)
		282:San Andreas (San Bernardino N)
		283:San Andreas (San Bernardino S)
		284:San Andreas (San Gorgonio Pass-Garnet HIll)
		295:San Andreas (Coachella) rev*/
		ArrayList<Integer> faultSectionIds = new ArrayList<Integer>();
		faultSectionIds.add(32);
		faultSectionIds.add(285);
		faultSectionIds.add(300);
		faultSectionIds.add(287);
		faultSectionIds.add(286);
		faultSectionIds.add(301);
		faultSectionIds.add(282);
		faultSectionIds.add(283);
		faultSectionIds.add(284);
		faultSectionIds.add(295);
		
		subSectionList = new ArrayList<FaultSectionPrefData>();		
		for(int i=0; i<faultSectionIds.size(); ++i) {
			FaultSectionPrefData faultSectionPrefData = 
				deformationModelPrefDB_DAO.getFaultSectionPrefData(deformationModelId, faultSectionIds.get(i));
			subSectionList.addAll(faultSectionPrefData.getSubSectionsList(this.MAX_SUBSECTION_LEN));
		}
	}

	
	
	/**
	 * Get a list of all subsections
	 * 
	 * @return
	 */
	public ArrayList<FaultSectionPrefData> getAllSubsections() {
		return this.subSectionList;
	}
	
	
	private final static int[][] getRupInSegMatrix(int num_seg) {
		
		int num_rup = num_seg*(num_seg+1)/2;
		int[][] rupInSeg = new int[num_seg][num_rup];
		
		int n_rup_wNseg = num_seg;
		int remain_rups = num_seg;
		int nSegInRup = 1;
		int startSeg = 0;
		for(int rup = 0; rup < num_rup; rup += 1) {
			for(int seg = startSeg; seg < startSeg+nSegInRup; seg += 1)
				rupInSeg[seg][rup] = 1;
			startSeg += 1;
			remain_rups -= 1;
			if(remain_rups == 0) {
				startSeg = 0;
				nSegInRup += 1;
				n_rup_wNseg -= 1;
				remain_rups = n_rup_wNseg;
			}
		}
		
		// check result
		/*
		if(D) {
			for(int seg = 0; seg < num_seg; seg+=1) {
				System.out.print("\n");
				for(int rup = 0; rup < num_rup; rup += 1)
					System.out.print(rupInSeg[seg][rup]+"  ");
			}
			System.out.print("\n");
		}
		*/
		
		return rupInSeg;
	}
	
	/**
	 * 
	 */
	private void computeInitialStuff() {
		rupArea = new double[num_rup];
		segArea = new double[num_seg];
		segSlipRate = new double[num_seg];
		segSlipRateStdDev = new double[num_seg];
		segMoRate = new double[num_seg];
		double minLength = Double.MAX_VALUE;
		double maxLength = 0;
		double minArea = Double.MAX_VALUE;
		double maxArea = 0;
		FaultSectionPrefData segData;
		for(int seg=0; seg < num_seg; seg++) {
				segData = subSectionList.get(seg);
				segArea[seg] = segData.getDownDipWidth()*segData.getLength()*1e6*(1.0-segData.getAseismicSlipFactor()); // km --> m 
				segSlipRate[seg] = segData.getAveLongTermSlipRate()*1e-3; // mm/yr --> m/yr
				segSlipRateStdDev[seg] = segData.getSlipRateStdDev()*1e-3; // mm/yr --> m/yr
//				System.out.println(seg+":  segData.getLength()=\t"+segData.getLength());


//				if(D) System.out.println(seg+" slip rate = "+segSlipRate[seg]);
				segMoRate[seg] = FaultMomentCalc.getMoment(segArea[seg], segSlipRate[seg]); // 
				
				if(segData.getLength() < minLength) minLength = segData.getLength();
				if(segData.getLength() > maxLength) maxLength = segData.getLength();
				if(segArea[seg]/1e6 < minArea) minArea = segArea[seg]/1e6;
				if(segArea[seg]/1e6 > maxArea) maxArea = segArea[seg]/1e6;
		}
		if(D) System.out.println("minSegArea="+(float)minArea+"\nmaxSegArea="+(float)maxArea+"\nminSegLength="+(float)minLength+"\nmaxSegLength="+(float)maxLength);
		
		for(int rup=0; rup<num_rup; rup++){
			rupArea[rup] = 0;
			for(int seg=0; seg < num_seg; seg++)
				if(rupInSeg[seg][rup]==1)  rupArea[rup] += segArea[seg];
		}
	}
	
	
	/**
	 * This creates the segSlipInRup (Dsr) matrix based on the value of slipModelType.
	 * This slips are in meters.
	 *
	 */
	private void computeSegSlipInRupMatrix() {
		segSlipInRup = new double[num_seg][num_rup];
		FaultSectionPrefData segData;
		
		// for case segment slip is independent of rupture, and equal to slip-rate * MRI
		// note that we're using the event rates that include the min constraint (segRateFromAprioriWithMinRateConstr)
		if(slipModelType.equals(CHAR_SLIP_MODEL)) {
			throw new RuntimeException(CHAR_SLIP_MODEL+ " not yet supported");
			/*
			for(int seg=0; seg<num_seg; seg++) {
				double segCharSlip = segmentData.getSegmentSlipRate(seg)*(1-moRateReduction)/segRateFromAprioriWithMinRateConstr[seg];
				for(int rup=0; rup<num_rup; ++rup) {
					segSlipInRup[seg][rup] = rupInSeg[seg][rup]*segCharSlip;
				}
			}
			*/
		}
		// for case where ave slip computed from mag & area, and is same on all segments 
		else if (slipModelType.equals(UNIFORM_SLIP_MODEL)) {
			for(int rup=0; rup<num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]/(rupArea[rup]*FaultMomentCalc.SHEAR_MODULUS);  // inlcudes aveSlipCorr
				for(int seg=0; seg<num_seg; seg++) {
					segSlipInRup[seg][rup] = rupInSeg[seg][rup]*aveSlip;
				}
			}
		}
		// this is the model where seg slip is proportional to segment slip rate 
		// (bumped up or down based on ratio of seg slip rate over wt-ave slip rate (where wts are seg areas)
		else if (slipModelType.equals(WG02_SLIP_MODEL)) {
			for(int rup=0; rup<num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]/(rupArea[rup]*FaultMomentCalc.SHEAR_MODULUS);    // inlcudes aveSlipCorr
				double totMoRate = 0;	// a proxi for slip-rate times area
				double totArea = 0;
				for(int seg=0; seg<num_seg; seg++) {
					if(rupInSeg[seg][rup]==1) {
						totMoRate += segMoRate[seg]; // a proxi for Vs*As
						totArea += segArea[seg];
					}
				}
				for(int seg=0; seg<num_seg; seg++) {
					segSlipInRup[seg][rup] = aveSlip*rupInSeg[seg][rup]*segMoRate[seg]*totArea/(totMoRate*segArea[seg]);
				}
			}
		}
		else if (slipModelType.equals(TAPERED_SLIP_MODEL)) {
			// note that the ave slip is partitioned by area, not length; this is so the final model is moment balanced.
			mkTaperedSlipFuncs();
			for(int rup=0; rup<num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]/(rupArea[rup]*FaultMomentCalc.SHEAR_MODULUS);    // inlcudes aveSlipCorr
//System.out.println(rup+"\t"+(float)aveSlip+" m");
				double normBegin=0, normEnd, scaleFactor;
				for(int seg=0; seg<num_seg; seg++) {
					if(rupInSeg[seg][rup]==1) {
						normEnd = normBegin + segArea[seg]/rupArea[rup];
						// fix normEnd values that are just past 1.0
						if(normEnd > 1 && normEnd < 1.00001) normEnd = 1.0;
						scaleFactor = taperedSlipCDF.getInterpolatedY(normEnd)-taperedSlipCDF.getInterpolatedY(normBegin);
						scaleFactor /= (normEnd-normBegin);
						segSlipInRup[seg][rup] = aveSlip*scaleFactor;
						normBegin = normEnd;
					}
				}
				/*
				if(D) { // check results
					double d_aveTest=0;
					for(int seg=0; seg<num_seg; seg++)
						d_aveTest += segSlipInRup[seg][rup]*segArea[seg]/rupArea[rup];
					System.out.println("AveSlipCheck: " + (float) (d_aveTest/aveSlip));
				}
				*/
			}
		}
		else throw new RuntimeException("slip model not supported");
	}
	
	
	/**
	 * This makes a tapered slip function based on the [Sin(x)]^0.5 fit of 
	 * Biasi & Weldon (in prep; pesonal communication), which is based on  
	 * the data comilation of Biasi & Weldon (2006, "Estimating Surface  
	 * Rupture Length and Magnitude of Paleoearthquakes from Point 
	 * Measurements of Rupture Displacement", Bull. Seism. Soc. Am. 96, 
	 * 1612-1623, doi: 10.1785/0120040172 E)
	 *
	 */
	private static void mkTaperedSlipFuncs() {
		
		// only do if another instance has not already done this
		if(taperedSlipCDF != null) return;
		
		taperedSlipCDF = new EvenlyDiscretizedFunc(0, 51, 0.02);
		taperedSlipPDF = new EvenlyDiscretizedFunc(0, 51, 0.02);
		double x,y, sum=0;
		int num = taperedSlipPDF.getNum();
		for(int i=0; i<num;i++) {
			x = taperedSlipPDF.getX(i);
			// y = Math.sqrt(1-(x-0.5)*(x-0.5)/0.25);
			y = Math.pow(Math.sin(x*Math.PI), 0.5);
			taperedSlipPDF.set(i,y);
			sum += y;
		}

		// now make final PDF & CDF
		y=0;
		for(int i=0; i<num;i++) {
				y += taperedSlipPDF.getY(i);
				taperedSlipCDF.set(i,y/sum);
				taperedSlipPDF.set(i,taperedSlipPDF.getY(i)/sum);
//				System.out.println(taperedSlipCDF.getX(i)+"\t"+taperedSlipPDF.getY(i)+"\t"+taperedSlipCDF.getY(i));
		}
	}

	
	// This gets the seg-rate constraints by associating locations from Appendix C to those sub-sections created here
	private void computeSegRateConstraints() {
		segRateConstraints   = new ArrayList<SegRateConstraint>();
		try {				
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(SEG_RATE_FILE_NAME));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet sheet = wb.getSheetAt(0);
			int lastRowIndex = sheet.getLastRowNum();
			double lat, lon, rate, sigma, lower95Conf, upper95Conf;
			String siteName;
			for(int r=1; r<=lastRowIndex; ++r) {	
				
				// read the event from the file
				HSSFRow row = sheet.getRow(r);
				if(row==null) continue;
				HSSFCell cell = row.getCell( (short) 1);
				if(cell==null || cell.getCellType()==HSSFCell.CELL_TYPE_STRING) continue;
				lat = cell.getNumericCellValue();
				siteName = row.getCell( (short) 0).getStringCellValue().trim();
				lon = row.getCell( (short) 2).getNumericCellValue();
				rate = row.getCell( (short) 3).getNumericCellValue();
				sigma =  row.getCell( (short) 4).getNumericCellValue();
				lower95Conf = row.getCell( (short) 7).getNumericCellValue();
				upper95Conf =  row.getCell( (short) 8).getNumericCellValue();
				
				// get Closest sub section
				double minDist = Double.MAX_VALUE, dist;
				int closestFaultSectionIndex=-1;
				Location loc = new Location(lat,lon);
				for(int sectionIndex=0; sectionIndex<subSectionList.size(); ++sectionIndex) {
					dist  = subSectionList.get(sectionIndex).getFaultTrace().minDistToLine(loc);
					if(dist<minDist) {
						minDist = dist;
						closestFaultSectionIndex = sectionIndex;
					}
				}
				if(minDist>2) continue; // closest fault section is at a distance of more than 2 km
				
				// add to Seg Rate Constraint list
				SegRateConstraint segRateConstraint = new SegRateConstraint(subSectionList.get(closestFaultSectionIndex).getSectionName());
				segRateConstraint.setSegRate(closestFaultSectionIndex, rate, sigma, lower95Conf, upper95Conf);
				segRateConstraints.add(segRateConstraint);
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
		
	}
	
	
	private void setAprioriRateData() {
		
		/* Set Parkfield sub-section ruptures (low mags due to high aseismicity)
		rup mag (H&B)
		0	5.2702227
		1	5.2702227
		2	5.2702227
		3	5.2702227
		58	5.5712523
		59	5.5712523
		60	5.5712523
		115	5.7473435
		116	5.7473435
		*/
		int[] parkSubSectRupIndices = {0,1,2,3,58,59,60,115,116};
		int num_constraints = parkSubSectRupIndices.length + 1; // 10;
		aPriori_rupIndex = new int[num_constraints];
		aPriori_rate = new double[num_constraints];
		aPriori_wt = new double[num_constraints];
		
		// set sub-segment parkfield rates to zero
		for(int rup=0; rup <parkSubSectRupIndices.length; rup++) {
			aPriori_rupIndex[rup] = parkSubSectRupIndices[rup];
			aPriori_rate[rup] = 0.0;
			aPriori_wt[rup] = 1e6; 
			
		}

		
		// Set parkfield rate to ~25 years
		aPriori_rupIndex[9] = 171;
		aPriori_rate[9] = 0.04; // 1/25
		aPriori_wt[9] = 1.0/0.01; 
		
		
	}

	
	private void setMinRates() {
		minRates = new double[num_rup]; // this sets them all to zero
		for(int rup=0; rup<num_rup; rup++) minRates[rup] = 1e-6;
	}
	
	/**
	 * This gets the non-negative least squares solution for the matrix C
	 * and data vector d.
	 * @param C
	 * @param d
	 * @return
	 */
	private static double[] getNNLS_solution(double[][] C, double[] d) {

		int nRow = C.length;
		int nCol = C[0].length;
		
		double[] A = new double[nRow*nCol];
		double[] x = new double[nCol];
		
		int i,j,k=0;
	
		if(MATLAB_TEST) {
			System.out.println("display "+"SSAF Inversion test");
			System.out.println("C = [");
			for(i=0; i<nRow;i++) {
				for(j=0;j<nCol;j++) 
					System.out.print(C[i][j]+"   ");
				System.out.print("\n");
			}
			System.out.println("];");
			System.out.println("d = [");
			for(i=0; i<nRow;i++)
				System.out.println(d[i]);
			System.out.println("];");
		}
/////////////////////////////////////
		
		for(j=0;j<nCol;j++) 
			for(i=0; i<nRow;i++)	{
				A[k]=C[i][j];
				k+=1;
			}
		nnls.update(A,nRow,nCol);
		
		boolean converged = nnls.solve(d,x);
		if(!converged)
			throw new RuntimeException("ERROR:  NNLS Inversion Failed");
		
		if(MATLAB_TEST) {
			System.out.println("x = [");
			for(i=0; i<x.length;i++)
				System.out.println(x[i]);
			System.out.println("];");
			System.out.println("max(abs(x-lsqnonneg(C,d)))");
		}
		
		return x;
	}
	
	/**
	 * Computer Final Slip Rate for each segment (& aPrioriSegSlipRate)
	 *
	 */
	private void computeFinalStuff() {
		
		// compute segment slip and event rates
		finalSegSlipRate = new double[num_seg];
		finalSegEventRate = new double[num_seg];
		for(int seg=0; seg < num_seg; seg++) {
			finalSegSlipRate[seg] = 0;
			finalSegEventRate[seg] = 0;
			for(int rup=0; rup < num_rup; rup++) 
				if(rupInSeg[seg][rup]==1) {
					finalSegSlipRate[seg] += rupRateSolution[rup]*segSlipInRup[seg][rup];
					finalSegEventRate[seg]+=rupRateSolution[rup];
				}
//			System.out.println((float)(finalSegSlipRate[seg]/this.d_pred[seg]));
//			double absFractDiff = Math.abs(finalSegSlipRate[seg]/(segSlipRate[seg]*(1-this.moRateReduction)) - 1.0);	
		}
		
		// compute predicted data
		
		// compute segment slip-rate and event rate residuals
		
//		segSlipRateResids, segEventRateResids
		
		magFreqDist = new SummedMagFreqDist(5,41,0.1);
		magFreqDist.setTolerance(1.0); // set to large value so it becomes a histogram
		for(int rup=0; rup<num_rup;rup++) {
			magFreqDist.add(rupMeanMag[rup], rupRateSolution[rup]);
//			magFreqDist.add(rupMeanMag[rup], 1);			
		}
		magFreqDist.setName("Incremental Mag Freq Dist");
	}
	
	public void writeFinalStuff() {
		
		// write out rupture rates and mags
//		System.out.println("Final Rupture Rates & Mags:");
//		for(int rup=0; rup < num_rup; rup++)
//			System.out.println(rup+"\t"+(float)rupRateSolution[rup]+"\t"+(float)rupMeanMag[rup]);

		// write out final segment slip rates
			System.out.println("Segment Slip Rates: index, final, orig, and final/orig)");
			for(int seg = 0; seg < num_seg; seg ++) {
				double slipRate = segSlipRate[seg]*(1-this.moRateReduction);
				System.out.println(seg+"\t"+(float)finalSegSlipRate[seg]+"\t"+(float)slipRate+"\t"+(float)(finalSegSlipRate[seg]/slipRate));
			}
		
		// write out final segment event rates
		if(relativeSegRateWt > 0.0) {
			System.out.println("Segment Rates: index, final, orig, and final/orig)");
			SegRateConstraint constraint;
			for(int i = 0; i < segRateConstraints.size(); i ++) {
//				int row = firstRowSegEventRateData+i;
				constraint = segRateConstraints.get(i);
				int seg = constraint.getSegIndex();
//				System.out.println(seg+"\t"+(float)finalSegEventRate[seg]+"\t"+d_pred[row]+"\t"+(float)(finalSegEventRate[seg]/d_pred[row]));
				System.out.println(seg+"\t"+(float)finalSegEventRate[seg]+"\t"+(float)constraint.getMean()+"\t"+(float)(finalSegEventRate[seg]/constraint.getMean()));
			}
		}
		
		// write out final rates for ruptures with an a-priori constraint
		if(this.relative_aPrioriRupWt >0.0)
			System.out.println("A Priori Rates: index, final, orig, and final/orig)");
			for(int i=0; i<this.aPriori_rate.length;i++) {
//				int row = i+this.firstRowAprioriData;
//				System.out.println(aPriori_rupIndex[i]+"\t"+(float)rupRateSolution[aPriori_rupIndex[i]]+"\t"+d_pred[row]+"\t"+
//						(float)(rupRateSolution[aPriori_rupIndex[i]]/d_pred[row]));				
				System.out.println(aPriori_rupIndex[i]+"\t"+(float)rupRateSolution[aPriori_rupIndex[i]]+"\t"+aPriori_rate[i]+"\t"+
						(float)(rupRateSolution[aPriori_rupIndex[i]]/aPriori_rate[i]));				
			}
			
	}
	
	public void writePredErrorInfo() {
		
		// First without equation weights
		double totPredErr=0, slipRateErr=0, eventRateErr=0, aPrioriErr=0, smoothnessErr=0;
		for(int row=firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row++)
			slipRateErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*data_wt[row]*data_wt[row];
		
		if(relativeSegRateWt >0)
			for(int row=firstRowSegEventRateData; row <= lastRowSegEventRateData; row++)
				eventRateErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*data_wt[row]*data_wt[row];
		if(relative_aPrioriRupWt > 0)
			for(int row=firstRowAprioriData; row <= lastRowAprioriData; row++)
				aPrioriErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*data_wt[row]*data_wt[row];
		if(relative_smoothnessWt>0)
			for(int row=firstRowSmoothnessData; row <= lastRowSmoothnessData; row++)
				smoothnessErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*data_wt[row]*data_wt[row];
		totPredErr = slipRateErr+eventRateErr+aPrioriErr+smoothnessErr;
		System.out.println("\nTotal Prediction Error =\t"+(float)totPredErr+"\n\t"+
				"Slip Rate Err =\t\t"+(float)slipRateErr+"\trel. wt = 1.0\n\t"+
				"Event Rate Err =\t"+(float)eventRateErr+"\trel. wt = "+relativeSegRateWt+"\n\t"+
				"A Priori Err =\t\t"+(float)aPrioriErr+"\trel. wt = "+relative_aPrioriRupWt+"\n\t"+
				"Smoothness Err =\t"+(float)smoothnessErr+"\trel. wt = "+relative_smoothnessWt+"\n\t");
		
		// Now with equation weights
		totPredErr=0; slipRateErr=0; eventRateErr=0; aPrioriErr=0; smoothnessErr=0;
		for(int row=firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row++)
			slipRateErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*full_wt[row]*full_wt[row];
		if(relativeSegRateWt >0)
			for(int row=firstRowSegEventRateData; row <= lastRowSegEventRateData; row++)
				eventRateErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*full_wt[row]*full_wt[row];
		if(relative_aPrioriRupWt > 0)
			for(int row=firstRowAprioriData; row <= lastRowAprioriData; row++)
				aPrioriErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*full_wt[row]*full_wt[row];
		if(relative_smoothnessWt>0)
			for(int row=firstRowSmoothnessData; row <= lastRowSmoothnessData; row++)
				smoothnessErr += (d[row]-d_pred[row])*(d[row]-d_pred[row])*full_wt[row]*full_wt[row];
		totPredErr = slipRateErr+eventRateErr+aPrioriErr+smoothnessErr;
		System.out.println("\nTotal Pred Err w/ Eq Wts =\t"+(float)totPredErr+"\n\t"+
				"Slip Rate Err =\t\t"+(float)slipRateErr+"\trel. wt = 1.0\n\t"+
				"Event Rate Err =\t"+(float)eventRateErr+"\trel. wt = "+relativeSegRateWt+"\n\t"+
				"A Priori Err =\t\t"+(float)aPrioriErr+"\trel. wt = "+relative_aPrioriRupWt+"\n\t"+
				"Smoothness Err =\t"+(float)smoothnessErr+"\trel. wt = "+relative_smoothnessWt+"\n\t");
			
	}
	

	public void plotStuff() {
		
		// plot orig and final slip rates	
		double min = 0, max = num_seg-1;
		EvenlyDiscretizedFunc origSlipRateFunc = new EvenlyDiscretizedFunc(min, max, num_seg);
		EvenlyDiscretizedFunc finalSlipRateFunc = new EvenlyDiscretizedFunc(min, max, num_seg);
		for(int seg=0; seg<num_seg;seg++) {
			origSlipRateFunc.set(seg,segSlipRate[seg]*(1-moRateReduction));
			finalSlipRateFunc.set(seg,finalSegSlipRate[seg]);
		}
		ArrayList sr_funcs = new ArrayList();
		origSlipRateFunc.setName("Orig Slip Rates");
		finalSlipRateFunc.setName("Final Slip Rates");
		sr_funcs.add(origSlipRateFunc);
		sr_funcs.add(finalSlipRateFunc);
		GraphiWindowAPI_Impl sr_graph = new GraphiWindowAPI_Impl(sr_funcs, "Slip Rates");   

		// plot orig and final seg event rates	
		int num = segRateConstraints.size();
//		double min = 0, max = num_seg-1;
		EvenlyDiscretizedFunc origEventRateFunc = new EvenlyDiscretizedFunc(min, max, num_seg);
		EvenlyDiscretizedFunc finalEventRateFunc = new EvenlyDiscretizedFunc(min, max, num_seg);
		SegRateConstraint constraint;
		// fill in orig constraints
		for(int i = 0; i < num; i ++) {
			constraint = segRateConstraints.get(i);
			int seg = constraint.getSegIndex();
			origEventRateFunc.set(seg,constraint.getMean());
		}		
		// now fill in final event rates
		for(int seg=0;seg < num_seg; seg++)
			finalEventRateFunc.set(seg,finalSegEventRate[seg]);
		
		ArrayList er_funcs = new ArrayList();
		origEventRateFunc.setName("Orig Event Rates");
		finalEventRateFunc.setName("Final Event Rates");
		er_funcs.add(origEventRateFunc);
		er_funcs.add(finalEventRateFunc);
		GraphiWindowAPI_Impl er_graph = new GraphiWindowAPI_Impl(er_funcs, "Event Rates"); 
		
		
		// plot the final rupture rates
		max = num_rup-1;
		EvenlyDiscretizedFunc rupRateFunc = new EvenlyDiscretizedFunc(min, max, num_rup);
		for(int rup=0; rup<num_rup;rup++) {
			rupRateFunc.set(rup,rupRateSolution[rup]);
		}
		ArrayList rup_funcs = new ArrayList();
		rupRateFunc.setName("Rupture Rates");
		rup_funcs.add(rupRateFunc);
		GraphiWindowAPI_Impl rup_graph = new GraphiWindowAPI_Impl(rup_funcs, "Rupture Rates");   


		// plot MFD
		ArrayList mfd_funcs = new ArrayList();
		mfd_funcs.add(magFreqDist);
		EvenlyDiscretizedFunc cumMagFreqDist = magFreqDist.getCumRateDistWithOffset();
		cumMagFreqDist.setName("Cumulative Mag Freq Dist");
		mfd_funcs.add(cumMagFreqDist);
		GraphiWindowAPI_Impl mfd_graph = new GraphiWindowAPI_Impl(mfd_funcs, "Mag Freq Dists");   

	}

	
	/**
	 * It gets all the subsections for SoSAF and prints them on console
	 * @param args
	 */
	public static void main(String []args) {
		SoSAF_SubSectionInversion soSAF_SubSections = new  SoSAF_SubSectionInversion();
		
		
		System.out.println("Starting Inversion");
		String slipModelType = TAPERED_SLIP_MODEL;
		MagAreaRelationship magAreaRel = new HanksBakun2002_MagAreaRel();
		double relativeSegRateWt=1;
		double relative_aPrioriRupWt = 1;
		double relative_smoothnessWt = 1;
		boolean wtedInversion = true;
		soSAF_SubSections.doInversion(slipModelType, magAreaRel, relativeSegRateWt, relative_aPrioriRupWt, relative_smoothnessWt, wtedInversion);
		System.out.println("Done with Inversion");
		soSAF_SubSections.writeFinalStuff();
		soSAF_SubSections.writePredErrorInfo();
		soSAF_SubSections.plotStuff();
		
		
/*		
		ArrayList<FaultSectionPrefData> subsectionList = soSAF_SubSections.getAllSubsections();
		for(int i=0; i<subsectionList.size(); ++i) {
			FaultSectionPrefData subSection = subsectionList.get(i);
			System.out.println(i+"\t"+subSection.getSectionName()+"\t"+(float)subSection.getLength());
//			System.out.println(subSection.getFaultTrace());
		}
*/
		/*		
		// write rup names to a file
		System.out.println("Writing file for short rupture names");
		soSAF_SubSections.writeRupNames("ShortRupNames.txt");
		
		// computer and print seg Rate constraints
		System.out.println("Writing Seg Rate constraints");
		soSAF_SubSections.computeSegRateConstraints();
		for(int i=0; i<soSAF_SubSections.segRateConstraints.size(); ++i) {
			SegRateConstraint segRateConstraint = soSAF_SubSections.segRateConstraints.get(i);
			System.out.println(segRateConstraint.getFaultName()+","+segRateConstraint.getMean());
		}
*/	
		
	}

}
