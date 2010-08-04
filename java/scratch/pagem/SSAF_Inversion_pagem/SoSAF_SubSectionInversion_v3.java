/**
 * 
 */
package scratch.pagem.SSAF_Inversion_pagem;

import java.awt.Color;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
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
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.RunScript;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.SegRateConstraint;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphiWindowAPI_Impl;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;

/**
 * This class does an inversion for the rate of events in an unsegmented model:
 * 
 * TO DO:
 * 
 * 3) sample MRIs via monte carlo simulations (same for slip rates?) 4)
 * subsection to 5 km?
 * 
 */
public class SoSAF_SubSectionInversion_v3 {
	private final static String SEG_RATE_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/data/Appendix_C_Table7_091807.xls";
	public final static String ROOT_PATH = "/Users/pagem/eclipse/workspace/OpenSHA/scratchJavaDevelopers/pagem/SSAF_Inversion_pagem/";

	private boolean D = true;
	// private DeformationModelPrefDataDB_DAO deformationModelPrefDB = new
	// DeformationModelPrefDataDB_DAO(DB_AccessAPI.dbConnection);
	DeformationModelPrefDataFinal deformationModelPrefDB = new DeformationModelPrefDataFinal();

	public final static double GAUSS_MFD_SIGMA = 0.12;
	public final static double GAUSS_MFD_TRUNCATION = 2;

	private ArrayList<FaultSectionPrefData> subSectionList;

	private int num_seg, num_rup;

	private int[] numSegInRup, firstSegOfRup;
	private SummedMagFreqDist aveOfSegPartMFDs;

	private boolean transitionAseisAtEnds, transitionSlipRateAtEnds;
	private boolean slipRateConstraintAtSegCentersOnly;
	private int slipRateSmoothing;

	private double PARKFIELD_EVENT_RATE = 0.04;
	private double PARKFIELD_SEG_RATES = 0.04;

	// this accounts for fact that ave slip from Gauss MFD is greater than the
	// slip of the average mag
	private double gaussMFD_slipCorr;

	private int maxSubsectionLength;
	private int numSegForSmallestRups; // this sets the number of segments for
										// the smallest ruptures (either 1 or 2
										// for now).. e.g., if subsections are
										// ~5km, then we want at least two
										// rupturing at once.
	private String deformationModel;

	ArrayList<SegRateConstraint> segRateConstraints;

	int[] numSubSections; // this contains the number of subsections for each
							// section

	// a-priori rate constraints
	int[] aPriori_rupIndex;
	double[] aPriori_rate, aPriori_wt;

	private static boolean MATLAB_TEST = false;
	double[][] C_wted, C;
	double[] d, d_wted, data_wt, full_wt, d_pred; // the data vector

	private double minRates[]; // the minimum rate constraint for each rupture
	private double minRupRate;
	private boolean wtedInversion, applyProbVisible; // weight the inversion
														// according to slip
														// rate and segment rate
														// uncertainties
	private double relativeSegRateWt, relative_aPrioriRupWt,
			relative_smoothnessWt, relativeSlipRateSmoothnessWt, relative_aPrioriSegRateWt;
	private double relativeGR_constraintWt, grConstraintBvalue,
			grConstraintRateScaleFactor, smallestGR_constriantMag;

	private int firstRowSegSlipRateData = -1, firstRowSegEventRateData = -1,
			firstRowAprioriData = -1, firstRowSmoothnessData = -1, firstRowSlipRateSmoothnessData = -1;
	private int lastRowSegSlipRateData = -1, lastRowSegEventRateData = -1,
			lastRowAprioriData = -1, lastRowSmoothnessData = -1, lastRowSlipRateSmoothnessData = -1;
	private int firstRowGR_constraintData = -1, lastRowGR_constraintData = -1,
			firstRowParkSegConstraint = -1, lastRowParkSegConstraint = -1;
	private int totNumRows;

	// slip model:
	private String slipModelType;
	public final static String CHAR_SLIP_MODEL = "Characteristic (Dsr=Ds)";
	public final static String UNIFORM_SLIP_MODEL = "Uniform/Boxcar (Dsr=Dr)";
	public final static String WG02_SLIP_MODEL = "WGCEP-2002 model (Dsr prop to Vs)";
	public final static String TAPERED_SLIP_MODEL = "Tapered Ends ([Sin(x)]^0.5)";

	private static EvenlyDiscretizedFunc taperedSlipPDF, taperedSlipCDF;

	SummedMagFreqDist magFreqDist, meanMagHistorgram, magHistorgram;

	ArrayList<SummedMagFreqDist> segmentNucleationMFDs;
	ArrayList<SummedMagFreqDist> segmentParticipationMFDs;

	private int[][] rupInSeg;
	private double[][] segSlipInRup;

	private double[] finalSegEventRate, finalPaleoVisibleSegEventRate,
			finalSegSlipRate;
	private double[] segSlipRateResids, segEventRateResids;

	private String[] rupNameShort;
	private double[] rupArea, rupMeanMag, rupMeanMo, rupMoRate, totRupRate,
			segArea, segSlipRate, segSlipRateStdDev, segMoRate,
			rateOfRupEndsOnSeg;
	double[] rupRateSolution; // these are the rates from the inversion (not
								// total rate of MFD)
	double totMoRate;

	// the following is the total moment-rate reduction, including that which
	// goes to the
	// background, sfterslip, events smaller than the min mag here, and
	// aftershocks and foreshocks.
	private double moRateReduction;

	private MagAreaRelationship magAreaRel;

	// NNLS inversion solver - static to save time and memory
	private static NNLSWrapper nnls = new NNLSWrapper();

	public SoSAF_SubSectionInversion_v3() {

		// compute slip correction for Gaussian MFD
		GaussianMagFreqDist gDist1 = new GaussianMagFreqDist(5.0, 9.0, 41, 7,
				this.GAUSS_MFD_SIGMA, 1.0, this.GAUSS_MFD_TRUNCATION, 2);
		GaussianMagFreqDist gDist2 = new GaussianMagFreqDist(5.0, 9.0, 41, 7,
				0.01, 1.0, 0.01, 2);
		gDist1.scaleToCumRate(0, 1.0);
		gDist2.scaleToCumRate(0, 1.0);
		gaussMFD_slipCorr = gDist1.getTotalMomentRate()
				/ gDist2.getTotalMomentRate();
		// System.out.println("gaussMFD_slipCorr="+(float)gaussMFD_slipCorr+"\n");

		// this was to print out the PDF for the paper
		// gDist1.scaleToCumRate(0, 1.0);
		// System.out.println(gDist1.toString());

	}

	/**
	 * Write Short Rup names to a file
	 * 
	 * @param fileName
	 */
	public void writeRupNamesToFile(String fileName) {
		try {
			FileWriter fw = new FileWriter(
					"org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/rupCalc/"
							+ fileName);
			fw.write("rup_index\trupNameShort\n");
			for (int i = 0; i < rupNameShort.length; ++i)
				fw.write(i + "\t" + rupNameShort[i] + "\n");
			fw.close();
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * This writes the segPartMFDs to a file and, optionally, makes a GMT plot
	 * of the result (the latter only works on Ned's computer because GMT paths
	 * are hard coded)
	 * 
	 * @param dirName
	 * @param gmt_plot
	 */
	public void plotOrWriteSegPartMFDs(String dirName, boolean gmt_plot) {
		try {
			FileWriter fw = new FileWriter(ROOT_PATH + dirName
					+ "/segPartMFDsData.txt");
			FileWriter cfw = new FileWriter(ROOT_PATH + dirName
					+ "/segPartCumMFDsData" +
							String.valueOf(System.currentTimeMillis()) +
							".txt");		
			
			fw.write("seg_index\tmag\tpart_rate\n");
	//		cfw.write("seg_index\tmag\tpart_cum_rate\n");
			for (int s = 0; s < segmentParticipationMFDs.size(); s++) {
				SummedMagFreqDist mfd = segmentParticipationMFDs.get(s);
				EvenlyDiscretizedFunc cmfd = mfd.getCumRateDist();
				for (int m = 0; m < mfd.getNum(); m++) {
					if (mfd.getY(m) != 0.0)
						fw.write(s + "\t" + (float) mfd.getX(m) + "\t"
								+ (float) Math.log10(mfd.getY(m)) + "\n");
					if (cmfd.getY(m) != 0.0)
						cfw.write(s + "\t" + (float) cmfd.getX(m) + "\t"
								+ (float) Math.log10(cmfd.getY(m)) + "\n");
					// System.out.println(s+"\t"+(float)cmfd.getX(m)+"\t"+(float)Math.log10(mfd.getY(m))+"\t"+(float)Math.log10(cmfd.getY(m))+"\n");
				}
			}
			fw.close();
			cfw.close();
		} catch (Exception e) {
			e.printStackTrace();
		}

		if (gmt_plot) {
			String PATH = ROOT_PATH + dirName + "/";
			String gmtScriptName = PATH + "gmt_script.txt";
			String region = "-R/-1/" + num_seg + "/5.5/8.5";
			try {
				FileWriter fw = new FileWriter(gmtScriptName);
				/**/
				fw.write("/sw/bin/xyz2grd " + PATH + "segPartMFDsData.txt -G"
						+ PATH + "temp.grd -I1.0/0.1 " + region + " -H1\n");
				fw
						.write("/sw/bin/gmtset ANOT_FONT_SIZE 14p LABEL_FONT_SIZE 18p HEADER_FONT_SIZE 22p\n");
				fw.write("/sw/bin/grdimage " + PATH
						+ "temp.grd -X1.0i  -Y3i  -JX6i/3i  -C" + ROOT_PATH
						+ "final.cpt  -P -T  -E72 -K " + region + "  > " + PATH
						+ "plotSectMFDs.ps\n");
				fw
						.write("/sw/bin/psscale -Ba1.0:log10_Rate: -D3i/-1i/6i/0.3ih -C"
								+ ROOT_PATH
								+ "final.cpt -O -K -N70 >> "
								+ PATH
								+ "plotSectMFDs.ps\n");
				fw
						.write("/sw/bin/psbasemap -B5.0:sub_section:/0.5:mag:eWnS:.Incremental_Participcation_MFD:  -JX6i/3i  "
								+ region
								+ " -K -O  >> "
								+ PATH
								+ "plotSectMFDs.ps\n");
				// now add cum MFD plot
				fw.write("/sw/bin/xyz2grd " + PATH
						+ "segPartCumMFDsData.txt -G" + PATH
						+ "temp.grd -I1.0/0.1 " + region + " -H1\n");
				fw.write("/sw/bin/grdimage " + PATH
						+ "temp.grd -Y4i  -JX6i/3i  -C" + ROOT_PATH
						+ "final.cpt  -P -T  -E72 -K -O " + region + "  >> "
						+ PATH + "plotSectMFDs.ps\n");
				fw
						.write("/sw/bin/psbasemap -B5.0/0.5:mag:eWNs:.Cumulative_Participcation_MFD:  -JX6i/3i  "
								+ region
								+ "  -O  >> "
								+ PATH
								+ "plotSectMFDs.ps\n");

				// unfortunately neither of the following does not work from
				// here (but do work from command line)
				// fw.write("/Applications/Preview.app/*/MacOS/Preview
				// plotSectMFDs.ps");
				// fw.write("/sw/bin/ps2pdf "+PATH+"plot.ps
				// "+PATH+"plotSectMFDs.pdf\n");
				fw.close();
			} catch (Exception e) {
				e.printStackTrace();
			}
			// now run the GMT script file
			String[] command = { "sh", "-c", "sh " + gmtScriptName };
			RunScript.runScript(command);
		}

	}

	/**
	 * This writes the
	 * 
	 * @param dirName
	 * @param gmt_plot
	 */
	public void writeAndPlotNonZeroRateRups(String dirName, boolean gmt_plot) {

		int num = -1;
		double min = 1e16, max = 0;
		try {
			FileWriter fw = new FileWriter(ROOT_PATH + dirName
					+ "/rupSlipRateData.txt");
			FileWriter fw2 = new FileWriter(ROOT_PATH + dirName
					+ "/rupRateData"
					+ String.valueOf(System.currentTimeMillis())
					+ ".txt");
			fw.write("index\tseg_index\tslip_rate\n");
		//	fw2.write("index\tseg_index\trate\n");
			for (int rup = 0; rup < num_rup; rup++) {
			//	if (rupRateSolution[rup] > minRupRate) {
					num += 1;
					for (int s = 0; s < num_seg; s++)
						if (rupInSeg[s][rup] == 1) {
							double slipRate = segSlipInRup[s][rup]
									* rupRateSolution[rup];
							fw.write(s + "\t" + num + "\t"
									+ (float) Math.log10(slipRate) + "\n");
						//	fw2.write(s + "\t" + num + "\t"
						//			+ (float) Math.log10(rupRateSolution[rup])
						//			+ "\n");
							fw2.write(s+"\t"+num+"\t"+rupRateSolution[rup]+"\n");
							
							if (slipRate > max)
								max = slipRate;
							if (slipRate < min)
								min = slipRate;
						}
			//	}
			}
			fw.close();
			fw2.close();
		} catch (Exception e) {
			e.printStackTrace();
		}

		// System.out.println("HERE IT IS min="+min+"\tmax="+max);

		if (gmt_plot) {
			String PATH = ROOT_PATH + dirName + "/";
			String gmtScriptName = PATH + "gmt_script_for_rups.txt";
			num += 1;
			String region = "-R/-1/" + num_seg + "/-1/" + num;
			try {
				FileWriter fw = new FileWriter(gmtScriptName);
				/**/
				fw.write("/sw/bin/xyz2grd " + PATH + "rupSlipRateData.txt -G"
						+ PATH + "temp.grd -I1.0/1.0 " + region + " -H1\n");
				fw
						.write("/sw/bin/gmtset ANOT_FONT_SIZE 14p LABEL_FONT_SIZE 18p HEADER_FONT_SIZE 22p\n");
				fw.write("/sw/bin/grdimage " + PATH
						+ "temp.grd -X1.25i  -Y3i  -JX6i/7i  -C" + ROOT_PATH
						+ "final.cpt  -P -T -K " + region + "  > " + PATH
						+ "plotForRupSlipRates.ps\n");
				fw
						.write("/sw/bin/psscale -Ba1.0:log10_Rate: -D3i/-1i/6i/0.3ih -C"
								+ ROOT_PATH
								+ "final.cpt -O -K -N70 >> "
								+ PATH
								+ "plotForRupSlipRates.ps\n");
				fw
						.write("/sw/bin/psbasemap -B5.0:sub_section:/5:rupture:eWnS:.Rupture_Slip_Rates:  -JX6i/7i  "
								+ region
								+ " -O  >> "
								+ PATH
								+ "plotForRupSlipRates.ps\n");

				fw.write("/sw/bin/xyz2grd " + PATH + "rupRateData.txt -G"
						+ PATH + "temp.grd -I1.0/1.0 " + region + " -H1\n");
				fw.write("/sw/bin/grdimage " + PATH
						+ "temp.grd -X1.25i  -Y3i  -JX6i/7i  -C" + ROOT_PATH
						+ "final.cpt  -P -T -K " + region + "  > " + PATH
						+ "plotForRupRates.ps\n");
				fw
						.write("/sw/bin/psscale -Ba1.0:log10_Rate: -D3i/-1i/6i/0.3ih -C"
								+ ROOT_PATH
								+ "final.cpt -O -K -N70 >> "
								+ PATH
								+ "plotForRupRates.ps\n");
				fw
						.write("/sw/bin/psbasemap -B5.0:sub_section:/5:rupture:eWnS:.Rupture_Rates:  -JX6i/7i  "
								+ region
								+ " -O  >> "
								+ PATH
								+ "plotForRupRates.ps\n");

				// unfortunately neither of the following does not work from
				// here (but do work from command line)
				// fw.write("/Applications/Preview.app/*/MacOS/Preview
				// plotForRupSlipRates.ps");
				// fw.write("/sw/bin/ps2pdf "+PATH+"plotForRupSlipRates.ps
				// "+PATH+"plotForRupSlipRates.pdf\n");
				fw.close();
			} catch (Exception e) {
				e.printStackTrace();
			}
			// now run the GMT script file
			String[] command = { "sh", "-c", "sh " + gmtScriptName };
			RunScript.runScript(command);
		}

	}

	/**
	 * 
	 * @param maxSubsectionLength -
	 *            max length of sub-sections (5 or 10 km)
	 * @param numSegForSmallestRups -
	 *            the minimum number of subsections involved in the smallest
	 *            ruptures (2 if above is 5 km, or 1 if above is 10 km)
	 * @param deformationModel -
	 *            D2.1, D2.2, or D2.3
	 * @param slipModelType -
	 *            TAPERED_SLIP_MODEL, UNIFORM_SLIP_MODEL, or WG02_SLIP_MODEL
	 * @param magAreaRel
	 * @param relativeSegRateWt -
	 *            weight on segment rate equations (relative to slip rate)
	 * @param relative_aPrioriRupWt -
	 *            weight on a-priori rates (relative to slip rate)
	 * @param relative_smoothnessWt -
	 *            weight on smoothness equations (relative to slip rate)
	 * @param relativeSlipRateSmoothnessWt -
	 *            weight on slip rate smoothness equations (relative to slip rate)       
	 * @param wtedInversion -
	 *            apply data uncertainties?
	 * @param minRupRate -
	 *            constrain all rupture rates to be greater than this value
	 * @param applyProbVisible -
	 *            account for likelihood that Paleoseismology will see the
	 *            rupture
	 * @param moRateReduction -
	 *            fraction reduction from smaller events
	 * @param transitionAseisAtEnds -
	 *            linear taper aseismicity at ends?
	 * @param transitionSlipRateAtEnds -
	 *            linear taper slip rates at ends?
	 * @param slipRateConstraintAtSegCentersOnly
	 * 			   applies slip rate constraint to center of fault segments only if true
	 * @param slipRateSmoothing -
	 *            if > 1, this boxcar-smoothes slip rates over the number given
	 *            (use odd number)
	 */
	public void doInversion(int maxSubsectionLength, int numSegForSmallestRups,
			String deformationModel, String slipModelType,
			MagAreaRelationship magAreaRel, double relativeSegRateWt,
			double relative_aPrioriRupWt, double relative_smoothnessWt, double relativeSlipRateSmoothnessWt,
			boolean wtedInversion, double minRupRate, boolean applyProbVisible,
			double moRateReduction, boolean transitionAseisAtEnds,
			boolean transitionSlipRateAtEnds, boolean slipRateConstraintAtSegCentersOnly, int slipRateSmoothing,
			double relativeGR_constraintWt, double grConstraintBvalue,
			double grConstraintRateScaleFactor, double relative_aPrioriSegRateWt) {
		
		this.maxSubsectionLength = maxSubsectionLength;
		this.numSegForSmallestRups = numSegForSmallestRups;
		this.deformationModel = deformationModel;
		this.slipModelType = slipModelType;
		this.magAreaRel = magAreaRel;
		this.relativeSegRateWt = relativeSegRateWt;
		this.relative_aPrioriRupWt = relative_aPrioriRupWt;
		this.relative_smoothnessWt = relative_smoothnessWt;
		this.relativeSlipRateSmoothnessWt = relativeSlipRateSmoothnessWt;
		this.wtedInversion = wtedInversion;
		this.minRupRate = minRupRate;
		this.applyProbVisible = applyProbVisible;
		this.moRateReduction = moRateReduction;
		this.transitionAseisAtEnds = transitionAseisAtEnds;
		this.transitionSlipRateAtEnds = transitionSlipRateAtEnds;
		this.slipRateConstraintAtSegCentersOnly = slipRateConstraintAtSegCentersOnly;	
		this.slipRateSmoothing = slipRateSmoothing;		
		this.relativeGR_constraintWt = relativeGR_constraintWt;
		this.grConstraintBvalue = grConstraintBvalue;
		this.grConstraintRateScaleFactor = grConstraintRateScaleFactor;
		this.relative_aPrioriSegRateWt = relative_aPrioriSegRateWt;

		if (numSegForSmallestRups != 1 && numSegForSmallestRups != 2)
			throw new RuntimeException(
					"Error: numSegForSmallestRups must be 1 or 2!");

		// chop the SSAF into many sub-sections
		computeAllSubsections();

		if (transitionAseisAtEnds)
			transitionAseisAtEnds();

		if (transitionSlipRateAtEnds)
			transitionSlipRateAtEnds();

		if (slipRateSmoothing > 1 && slipRateConstraintAtSegCentersOnly == false)
			smoothSlipRates(slipRateSmoothing);
		/*
		 * // print out subsection lengths, final slipRates, and aseis factors
		 * for(int s=0; s < subSectionList.size(); s++)
		 * System.out.println(s+"\t"+(float)subSectionList.get(s).getLength()+"\t"+
		 * (float)subSectionList.get(s).getAveLongTermSlipRate()+"\t"+
		 * (float)subSectionList.get(s).getAseismicSlipFactor());
		 */

		// get the RupInSeg Matrix for the given number of segments
		num_seg = subSectionList.size();

		// get the matrix giving what sub-sections are involved in each rupture
		rupInSeg = getRupInSegMatrix(num_seg);

		num_rup = rupInSeg[1].length;

		System.out
				.println("num_seg=" + num_seg + "; num_rup=" + num_rup + "\n");

		// make short rupture names
		rupNameShort = new String[num_rup];
		for (int rup = 0; rup < num_rup; rup++) {
			boolean isFirst = true;
			for (int seg = 0; seg < num_seg; seg++) {
				if (rupInSeg[seg][rup] == 1) { // if this rupture is included
												// in this segment
					if (isFirst) { // append the section name to rupture name
						rupNameShort[rup] = "" + (seg);
						isFirst = false;
					} else {
						rupNameShort[rup] += "+" + (seg);
					}
				}
			}
			// if(D) System.out.println(rup+"\t"+rupNameShort[rup]);
		}

		// compute rupture areas etc
		computeInitialStuff();

		// create the segRateConstraints (from Paleoseismic data)
		getPaleoSegRateConstraints();

		// compute rupture mean mags
		if (slipModelType.equals(CHAR_SLIP_MODEL))
			// getRupMeanMagsAssumingCharSlip();
			throw new RuntimeException(CHAR_SLIP_MODEL
					+ " is not yet supported");
		else {
			// compute from mag-area relationship
			rupMeanMag = new double[num_rup];
			rupMeanMo = new double[num_rup];
			for (int rup = 0; rup < num_rup; rup++) {
				double mag = magAreaRel.getMedianMag(rupArea[rup] / 1e6);
				// round this to nearst 10th unit
				rupMeanMag[rup] = ((double) Math.round(10 * mag)) / 10.0;
				rupMeanMo[rup] = MomentMagCalc.getMoment(rupMeanMag[rup])
						* gaussMFD_slipCorr; // increased if magSigma >0
			}
		}

		// set the a-priori rup rates & wts now that mags are set
		setAprioriRupRates();

		// compute matrix of Dsr (slip on each segment in each rupture)
		computeSegSlipInRupMatrix();

		// get the number of segment rate constraints
		int numRateConstraints = segRateConstraints.size();

		// get the number of a-priori rate constraints
		int num_aPriori_constraints = aPriori_rupIndex.length;
		
		// set the number of slip rate smoothing constraints
		// leave out slip rate smoothing at fault intersections
		ArrayList<Integer> subsectionsToSkip = new ArrayList<Integer>();
		subsectionsToSkip.add(52); // San Jacinto-SSAF intersection
		int numSlipRateSmoothnessConstraints = num_seg-2-2*subsectionsToSkip.size(); 

		// set the minimum rupture rate constraints
		if (minRupRate > 0.0) {
			minRates = new double[num_rup]; // this sets them all to zero
			for (int rup = 0; rup < num_rup; rup++)
				minRates[rup] = minRupRate;
		}

		// set the number of GR constraints and mag range
		double largestGR_constriantMag = rupMeanMag[num_rup - 1]; // the
																	// largest
																	// rupture
		if (relativeGR_constraintWt > 0)
			System.out.println("\nGR constraint mags: "
					+ (float) smallestGR_constriantMag + "\t"
					+ (float) largestGR_constriantMag + "\n");
		int numGR_constraints = (int) Math
				.round((largestGR_constriantMag - smallestGR_constriantMag) / 0.1) + 1;

		int numParkfieldSegRateConstaints = numSubSections[0];

		// SET NUMBER OF ROWS AND IMPORTANT INDICES

		// segment slip-rates always used (for now)
		firstRowSegSlipRateData = 0;
		if (slipRateConstraintAtSegCentersOnly == false) 
			totNumRows = num_seg; 
		else 
			totNumRows = numSubSections.length;
		lastRowSegSlipRateData = totNumRows - 1;

		// add segment rate constraints if needed
		if (relativeSegRateWt > 0.0) {
			firstRowSegEventRateData = totNumRows;
			totNumRows += numRateConstraints;
			lastRowSegEventRateData = totNumRows - 1;
		}

		// add a-priori rate constraints if needed
		if (relative_aPrioriRupWt > 0.0) {
			firstRowAprioriData = totNumRows;
			totNumRows += num_aPriori_constraints;
			lastRowAprioriData = totNumRows - 1;
		}

		// add number of smoothness constraints (smoothness of rupture rates)
		if (relative_smoothnessWt > 0) {
			firstRowSmoothnessData = totNumRows;
			if (numSegForSmallestRups == 1)
				totNumRows += num_rup - num_seg;
			else
				// the case where numSegForSmallestRups=2
				totNumRows += num_rup - (num_seg - 1);
			lastRowSmoothnessData = totNumRows - 1;
		}

		// add number of slip rate smoothing constraints
		if (relativeSlipRateSmoothnessWt > 0) {
			firstRowSlipRateSmoothnessData = totNumRows;
			totNumRows += numSlipRateSmoothnessConstraints;
			lastRowSlipRateSmoothnessData = totNumRows - 1;
		}
			
		// add number of GR constraints
		if (relativeGR_constraintWt > 0) {
			firstRowGR_constraintData = totNumRows;
			// totNumRows += numGR_constraints;
			lastRowGR_constraintData = totNumRows - 1;

		}

		if (relative_aPrioriSegRateWt > 0) {
			firstRowParkSegConstraint = totNumRows;
			totNumRows += numParkfieldSegRateConstaints;
			lastRowParkSegConstraint = totNumRows - 1;
		}

		System.out.println("\nfirstRowSegEventRateData="
				+ firstRowSegEventRateData + ";\tfirstRowAprioriData="
				+ firstRowAprioriData + ";\tfirstRowSmoothnessData="
				+ firstRowSmoothnessData + ";\tfirstRowSlipRateSmoothnessData="
				+ firstRowSlipRateSmoothnessData + ";\tfirstRowGR_constraintData="
				+ firstRowGR_constraintData + ";\tfirstRowParkSegConstraint="
				+ firstRowParkSegConstraint + ";\ttotNumRows=" + totNumRows
				+ "\n");

		C = new double[totNumRows][num_rup];
		d = new double[totNumRows]; // data vector
		C_wted = new double[totNumRows][num_rup]; // wted version
		d_wted = new double[totNumRows]; // wted data vector

		data_wt = new double[totNumRows]; // data weights
		full_wt = new double[totNumRows]; // data weights
		d_pred = new double[totNumRows]; // predicted data vector

		// initialize wts to 1.0
		for (int i = 0; i < data_wt.length; i++)
			data_wt[i] = 1.0;

		// CREATE THE MODEL AND DATA MATRICES

		// first fill in the slip-rate constraints & wts
		int cmlNumRows = 0;
		int centerSegIndex = 0;
		for (int row = firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row++) {
			if (slipRateConstraintAtSegCentersOnly == false) {
				d[row] = segSlipRate[row] * (1 - moRateReduction);	
				if (wtedInversion)
					data_wt[row] = 1 / ((1 - moRateReduction) * segSlipRateStdDev[row]);
				for (int col = 0; col < num_rup; col++)
					C[row][col] = segSlipInRup[row][col]; 
				}
			else {
				centerSegIndex = numSubSections[row-firstRowSegSlipRateData]/2 + cmlNumRows;
				// System.out.println("centerSegIndex = " + centerSegIndex);
				d[row] = segSlipRate[centerSegIndex]*(1 - moRateReduction);
				if (wtedInversion)
					data_wt[row] = 1 / ((1 - moRateReduction) * segSlipRateStdDev[centerSegIndex]);
				for (int col = 0; col < num_rup; col++)
					C[row][col] = segSlipInRup[centerSegIndex][col];
				cmlNumRows += numSubSections[row-firstRowSegSlipRateData];
			}
		}
				
		
		// now fill in the segment event rate constraints if requested
		if (relativeSegRateWt > 0.0) {
			SegRateConstraint constraint;
			for (int i = 0; i < numRateConstraints; i++) {
				constraint = segRateConstraints.get(i);
				int seg = constraint.getSegIndex();
				int row = i + firstRowSegEventRateData;
				d[row] = constraint.getMean(); // this is the average
												// sub-section rate
				if (wtedInversion)
					data_wt[row] = 1 / constraint.getStdDevOfMean();
				for (int col = 0; col < num_rup; col++)
					if (applyProbVisible)
						C[row][col] = rupInSeg[seg][col]
								* getProbVisible(rupMeanMag[col]);
					else
						C[row][col] = rupInSeg[seg][col];
			}
		}
		// now fill in the a-priori rates if needed
		if (relative_aPrioriRupWt > 0.0) {
			for (int i = 0; i < num_aPriori_constraints; i++) {
				int row = i + firstRowAprioriData;
				int col = aPriori_rupIndex[i];
				d[row] = aPriori_rate[i];
				if (wtedInversion)
					data_wt[row] = aPriori_wt[i];
				C[row][col] = 1.0;
			}
		}
		// add the smoothness constraint on rupture rates
		if (relative_smoothnessWt > 0.0) {
			int row = firstRowSmoothnessData;
			int counter = 0;
			for (int rup = 0; rup < num_rup; rup++) {
				// check to see if the last segment is used by the rupture (skip
				// this last rupture if so)
				if (rupInSeg[num_seg - 1][rup] != 1) {
					d[row] = 0;
					C[row][rup] = 1.0;
					C[row][rup + 1] = -1.0;
					row += 1;
					counter += 1;
				}
				// else
				// System.out.println("REJECT:
				// row="+row+"\trup="+rup+"\tcounter="+counter);
			}
		}
		
		// add the smoothness constraint on slip rates
		if (relativeSlipRateSmoothnessWt > 0.0) {
			int row = firstRowSlipRateSmoothnessData-1;	
			for (int i=1; i<numSlipRateSmoothnessConstraints; i++) {
				if (subsectionsToSkip.contains(i)==false && subsectionsToSkip.contains(i-1)==false) {
					row++;
					for (int col = 0; col < num_rup; col++) 
						C[row][col] = - segSlipInRup[i-1][col] + 2 * segSlipInRup[i][col] - segSlipInRup[i+1][col];
					//	C[row][col] = segSlipInRup[i-2][col] - 4 * segSlipInRup[i-1][col] + 6 * segSlipInRup[i][col] - 4 * segSlipInRup[i+1][col] + segSlipInRup[i+2][col];
					d[row]=0;
				}
			}
		}
		
		
		
		// System.out.println("num_smooth_constrints="+num_smooth_constrints);
		// now fill in the GR constraint if needed
		if (relativeGR_constraintWt > 0.0) {
			double deltaMag = 0.1;
			// create a GR dist with the target moment rate & max mag as an
			// estimate of absolute rates
			GutenbergRichterMagFreqDist gr = new GutenbergRichterMagFreqDist(5,
					41, deltaMag);
			gr.setAllButTotCumRate(5, largestGR_constriantMag, totMoRate,
					grConstraintBvalue);
			double totRate = gr.getTotCumRate();
			// grConstraintRateScaleFactor adjusts the a-value up or down
			gr.scaleToCumRate(0, totRate * grConstraintRateScaleFactor); 

			System.out.println("GR Constraint's Incremental Rate At M=6.5:\t"
					+ (float) gr.getIncrRate(6.5) + "\t");
			for (int i = 0; i < numGR_constraints; i++) {
				int row = i + firstRowGR_constraintData;
				double mag = smallestGR_constriantMag + i * deltaMag;
				d[row] = gr.getY(mag);
				// if(wtedInversion) {
				// data_wt[row] = Math.pow(10,
				// grConstraintBvalue*(mag-smallestGR_constriantMag)); // give
				// the larger events higher weight so those rates don't wander
				// System.out.println(mag+"\t"+(float)d[row]);
				// }
				for (int col = 0; col < num_rup; col++)
					if (rupMeanMag[col] < mag + 0.001
							&& rupMeanMag[col] > mag - 0.001)
						C[row][col] = 1.0;
			}
		}
		// add the Parkfield seg-rate constraints
		if (relative_aPrioriSegRateWt > 0.0) {
			double rate = PARKFIELD_SEG_RATES;
			int row = firstRowParkSegConstraint;
			for (int seg = 0; seg < numParkfieldSegRateConstaints; seg++) {
				d[row] = rate;
				for (int rup = 0; rup < num_rup; rup++)
					if (rupInSeg[seg][rup] == 1)
						C[row][rup] = 1.0;
				row += 1;
			}
		}

		// copy un-wted data to wted versions (wts added below)
		for (int row = 0; row < totNumRows; row++) {
			d_wted[row] = d[row];
			for (int col = 0; col < num_rup; col++)
				C_wted[row][col] = C[row][col];
		}

		// CORRECT IF MINIMUM RATE CONSTRAINT DESIRED
		if (minRupRate > 0.0) {
			double[] Cmin = new double[totNumRows]; // the data vector
			// correct the data vector
			for (int row = 0; row < totNumRows; row++) {
				for (int col = 0; col < num_rup; col++)
					Cmin[row] += minRates[col] * C_wted[row][col];
				d_wted[row] -= Cmin[row];
			}
		}

		// APPLY WEIGHTS

		// segment slip rates first (no equation-set weight because others are
		// relative)
		for (int row = firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row++) {
			if (wtedInversion)
				full_wt[row] = data_wt[row];
			else
				full_wt[row] = 1.0;
			d_wted[row] *= full_wt[row];
			for (int col = 0; col < num_rup; col++)
				C_wted[row][col] *= full_wt[row];
		}
		// segment event rate wts
		if (relativeSegRateWt > 0.0) {
			for (int i = 0; i < numRateConstraints; i++) {
				int row = i + firstRowSegEventRateData;
				full_wt[row] = relativeSegRateWt;
				if (wtedInversion)
					full_wt[row] *= data_wt[row];
				d_wted[row] *= full_wt[row];
				for (int col = 0; col < num_rup; col++)
					C_wted[row][col] *= full_wt[row];
			}
		}
		// a-priori rate wts
		if (relative_aPrioriRupWt > 0.0) {
			for (int i = 0; i < num_aPriori_constraints; i++) {
				int row = i + firstRowAprioriData;
				int col = aPriori_rupIndex[i];
				full_wt[row] = relative_aPrioriRupWt;
				if (wtedInversion)
					full_wt[row] *= data_wt[row];
				d_wted[row] *= full_wt[row];
				C_wted[row][col] = full_wt[row];
			}
		}
		// rupture rate smoothness constraint wts
		if (relative_smoothnessWt > 0.0) {
			int row = firstRowSmoothnessData;
			for (int rup = 0; rup < num_rup; rup++) {
				// check to see if the last segment is used by the rupture (skip
				// this last rupture if so)
				if (rupInSeg[num_seg - 1][rup] != 1) {
					full_wt[row] = relative_smoothnessWt;
					d_wted[row] *= full_wt[row];
					C_wted[row][rup] *= full_wt[row];
					C_wted[row][rup + 1] *= full_wt[row];
					row += 1;
				}
			}
		}
		// slip rate smoothness constraint wts
		if (relativeSlipRateSmoothnessWt > 0.0) {
			for (int i = 0; i < numSlipRateSmoothnessConstraints; i++) {
				int row = i + firstRowSlipRateSmoothnessData;
				full_wt[row] = relativeSlipRateSmoothnessWt;
				d_wted[row] *= full_wt[row];
				for (int rup = 0; rup < num_rup; rup++)
					C_wted[row][rup] *= full_wt[row];
			}
		}	
		
		// GR constraint wts
		if (relativeGR_constraintWt > 0.0) {
			for (int i = 0; i < numGR_constraints; i++) {
				int row = i + firstRowGR_constraintData;
				full_wt[row] = relativeGR_constraintWt;
				// if(wtedInversion) full_wt[row] *= data_wt[row];
				d_wted[row] *= full_wt[row];
				for (int rup = 0; rup < num_rup; rup++)
					C_wted[row][rup] *= full_wt[row];
			}
		}

		// add the Parkfield seg-rate constraints
		if (relative_aPrioriSegRateWt > 0.0) {
			int row = firstRowParkSegConstraint;
			for (int seg = 0; seg < numParkfieldSegRateConstaints; seg++) {
				full_wt[row] = relative_aPrioriSegRateWt;
				d_wted[row] *= full_wt[row];
				for (int rup = 0; rup < num_rup; rup++)
					if (rupInSeg[seg][rup] == 1)
						C_wted[row][rup] *= full_wt[row];
				row += 1;
			}
		}

		// for(int row=0;row<totNumRows; row++)
		// System.out.println(row+"\t"+(float)d[row]);

		/*
		 * // manual check of matrices int nRow = C.length; int nCol =
		 * C[0].length; System.out.println("C = ["); for(int i=0; i<nRow;i++) {
		 * for(int j=0;j<nCol;j++) System.out.print(C[i][j]+" ");
		 * System.out.print("\n"); } System.out.println("];");
		 * System.out.println("d = ["); for(int i=0; i<nRow;i++)
		 * System.out.println(d[i]); System.out.println("];");
		 */

		// SOLVE THE INVERSE PROBLEM
		// rupRateSolution = getNNLS_solution(C_wted, d_wted);
		rupRateSolution = getSimulatedAnnealing_solution(C_wted, d_wted);
		
		//System.out.print("\n");
		//System.out.print("rupRateSolution:\n");
		//for (int col = 0; col < num_rup; col++)
		//	System.out.println(rupRateSolution[col]);
		//System.out.print("\n");               
		
		// CORRECT FINAL RATES IF MINIMUM RATE CONSTRAINT APPLIED
		if (minRupRate > 0.0)
			for (int rup = 0; rup < num_rup; rup++)
				rupRateSolution[rup] += minRates[rup];

		// compute predicted data
		for (int row = 0; row < totNumRows; row++)
			for (int col = 0; col < num_rup; col++)
				d_pred[row] += rupRateSolution[col] * C[row][col];

		// Compute final segment slip rates and event rates
		computeFinalStuff();

		computeSegMFDs();

	}

	/**
	 * Get a list of all subsections
	 * 
	 * @return
	 */
	private void computeAllSubsections() {
		/**
		 * Set the deformation model D2.1 = 82 D2.2 = 83 D2.3 = 84 D2.4 = 85
		 * D2.5 = 86 D2.6 = 87
		 */
		int deformationModelId;
		if (deformationModel.equals("D2.1"))
			deformationModelId = 82;
		else if (deformationModel.equals("D2.2"))
			deformationModelId = 83;
		else if (deformationModel.equals("D2.3"))
			deformationModelId = 84;
		else
			throw new RuntimeException(
					"Error: Deformation model must be D2.1, D2.2, or D2.3");

		/*
		 * These are the same for D2.1, D2.2, and D2.3 32:San Andreas
		 * (Parkfield) 285:San Andreas (Cholame) rev 300:San Andreas (Carrizo)
		 * rev 287:San Andreas (Big Bend) 286:San Andreas (Mojave N) 301:San
		 * Andreas (Mojave S) 282:San Andreas (San Bernardino N) 283:San Andreas
		 * (San Bernardino S) 284:San Andreas (San Gorgonio Pass-Garnet HIll)
		 * 295:San Andreas (Coachella) rev
		 */
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

		// this will store the number of subsections for the ith section in the
		// list
		numSubSections = new int[faultSectionIds.size()];

		subSectionList = new ArrayList<FaultSectionPrefData>();
		int lastNum = 0;
		for (int i = 0; i < faultSectionIds.size(); ++i) {
			FaultSectionPrefData faultSectionPrefData = deformationModelPrefDB
					.getFaultSectionPrefData(deformationModelId,
							faultSectionIds.get(i));
			subSectionList.addAll(faultSectionPrefData
					.getSubSectionsList(this.maxSubsectionLength));
			// compute & write the number of subsections for this section
			numSubSections[i] = subSectionList.size() - lastNum;
			// System.out.println(faultSectionPrefData.getSectionName()+"\t"+subSectionList.size());
			// System.out.println(faultSectionPrefData.getSectionName()+"\t"+numSubSections[i]);
			lastNum = subSectionList.size();

			/*
			 * // write out section data
			 * System.out.print(faultSectionPrefData.getSectionName()+"\t");
			 * FaultTrace ft = faultSectionPrefData.getFaultTrace(); for(int
			 * l=0; l<ft.getNumLocations(); l++)
			 * System.out.print((float)ft.getLocationAt(l).getLatitude()+","+(float)ft.getLocationAt(l).getLongitude()+",");
			 * System.out.println("\t"+(float)faultSectionPrefData.getAveDip()+"\t"+
			 * (float)faultSectionPrefData.getDownDipWidth()+"\t"+
			 * (float)faultSectionPrefData.getLength()+"\t"+
			 * (float)faultSectionPrefData.getAveLongTermSlipRate()+"\t"+
			 * (float)faultSectionPrefData.getSlipRateStdDev()+"\t"+
			 * (float)faultSectionPrefData.getAseismicSlipFactor()+"\t");
			 */
		}

	}

	private void transitionAseisAtEnds() {
		FaultSectionPrefData segData;

		/**/
		// transition aseismicity factors for Parkfield sections
		// the math here represents a linear trend intersecting the zero value
		// in the subsection just after
		// the last one here, plus the constraint the the total ave value equal
		// the original
		int numSubSectForParkfield = numSubSections[0]; // Coachella
		double origAseis = subSectionList.get(0).getAseismicSlipFactor(); // the
																			// value
																			// is
																			// currently
																			// the
																			// same
																			// for
																			// all
																			// subsections
		double sumOfIndex = 0;
		for (int i = 0; i < numSubSectForParkfield; i++)
			sumOfIndex += i;
		double slope = (origAseis - 1)
				/ (sumOfIndex / numSubSectForParkfield - numSubSectForParkfield);
		double intercept = 1 - slope * numSubSectForParkfield;
		for (int i = 0; i < numSubSectForParkfield; i++) {
			segData = subSectionList.get(i);
			segData.setAseismicSlipFactor(slope
					* (numSubSectForParkfield - 1 - i) + intercept);
		}
		// check values
		double totProd = 0, totArea = 0;
		for (int seg = 0; seg < numSubSectForParkfield; seg++) {
			segData = subSectionList.get(seg);
			totArea += segData.getLength() * segData.getDownDipWidth();
			totProd += segData.getLength() * segData.getDownDipWidth()
					* segData.getAseismicSlipFactor();
			// System.out.println(seg+"\t"+(float)segData.getAveLongTermSlipRate()+"\t"+(float)segData.getAseismicSlipFactor()+
			// "\t"+(float)segData.getLength()+
			// "\t"+(float)segData.getDownDipWidth());
		}
		// System.out.println("Check on orig and final aseis for Parkfield
		// (values should be equal):
		// "+(float)origAseis+"\t"+(float)(totProd/totArea));

		// transition aseismicity factors for Coachella sections
		// the math here represents a linear trend from the zero value in the
		// subsection just before
		// the first one here, plus the constraint the the total ave value equal
		// the original
		int totNumSubSections = subSectionList.size();
		int numSubSectForCoachella = numSubSections[numSubSections.length - 1]; // Coachella
		origAseis = subSectionList.get(totNumSubSections - 1)
				.getAseismicSlipFactor(); // the value is currently the same
											// for all subsections
		sumOfIndex = 0;
		for (int i = 0; i < numSubSectForCoachella; i++)
			sumOfIndex += i;
		slope = origAseis / (sumOfIndex / numSubSectForCoachella + 1);
		intercept = slope;
		for (int i = totNumSubSections - numSubSectForCoachella; i < totNumSubSections; i++) {
			segData = subSectionList.get(i);
			segData.setAseismicSlipFactor(slope
					* (i - totNumSubSections + numSubSectForCoachella)
					+ intercept);
		}
		// check values
		totProd = 0;
		totArea = 0;
		for (int seg = totNumSubSections - numSubSectForCoachella; seg < totNumSubSections; seg++) {
			segData = subSectionList.get(seg);
			totArea += segData.getLength() * segData.getDownDipWidth();
			totProd += segData.getLength() * segData.getDownDipWidth()
					* segData.getAseismicSlipFactor();
			// System.out.println(seg+"\t"+(float)segData.getAveLongTermSlipRate()+"\t"+(float)segData.getAseismicSlipFactor()+
			// "\t"+(float)segData.getLength()+
			// "\t"+(float)segData.getDownDipWidth());
		}
		// System.out.println("Check on orig and final aseis for Coachella
		// (values should be equal):
		// "+(float)origAseis+"\t"+(float)(totProd/totArea));

		/*
		 * write out segment data for(int seg=0; seg < subSectionList.size();
		 * seg++) { segData = subSectionList.get(seg);
		 * System.out.println(seg+"\t"+(float)segData.getAveLongTermSlipRate()+"\t"+(float)segData.getAseismicSlipFactor()+
		 * "\t"+(float)segData.getLength()+
		 * "\t"+(float)segData.getDownDipWidth()); }
		 */
	}

	/**
	 * linearly transition the slip rates at the ends of the fault. This goes
	 * from the max slip rate at the most inner subsection point to a value of
	 * slipRate/N at the last end point, where N is the number of points in the
	 * subsection.
	 */
	private void transitionSlipRateAtEnds() {
		FaultSectionPrefData segData;

		// write out the original data
		/*
		 * for(int seg=0; seg < subSectionList.size(); seg++) { segData =
		 * subSectionList.get(seg);
		 * System.out.println(seg+"\t"+(float)segData.getAveLongTermSlipRate()+"\t"+(float)segData.getAseismicSlipFactor()+
		 * "\t"+(float)segData.getLength()+
		 * "\t"+(float)segData.getDownDipWidth()); }
		 */

		int numSubSectForParkfield = numSubSections[0]; // Parkfield
		double origSlipRate = subSectionList.get(0).getAveLongTermSlipRate(); // the
																				// value
																				// is
																				// currently
																				// the
																				// same
																				// for
																				// all
																				// subsections
		for (int i = 0; i < numSubSectForParkfield; i++) {
			segData = subSectionList.get(i);
			segData.setAveLongTermSlipRate(origSlipRate * (i + 1)
					/ numSubSectForParkfield);
			// System.out.println(i+"\t"+origSlipRate+"\t"+segData.getAveLongTermSlipRate());
		}

		int totNumSubSections = subSectionList.size();
		int numSubSectForCoachella = numSubSections[numSubSections.length - 1]; // Coachella
		origSlipRate = subSectionList.get(totNumSubSections - 1)
				.getAveLongTermSlipRate(); // the value is currently the same
											// for all subsections
		for (int i = totNumSubSections - numSubSectForCoachella; i < totNumSubSections; i++) {
			segData = subSectionList.get(i);
			segData.setAveLongTermSlipRate(origSlipRate
					* (totNumSubSections - i) / numSubSectForCoachella);
			// System.out.println(i+"\t"+origSlipRate+"\t"+segData.getAveLongTermSlipRate());
		}
	}

	/*
	 * This needs to be an odd number?
	 */
	private void smoothSlipRates(int numPts) {

		double[] slipRate = new double[subSectionList.size()];
		double[] smoothSlipRate = new double[subSectionList.size()];

		int n_seg = subSectionList.size();

		for (int seg = 0; seg < n_seg; seg++) {
			slipRate[seg] = subSectionList.get(seg).getAveLongTermSlipRate();
			smoothSlipRate[seg] = subSectionList.get(seg)
					.getAveLongTermSlipRate();
		}

		for (int seg = numPts; seg < n_seg; seg++) {
			double ave = 0;
			for (int i = seg - numPts; i < seg; i++)
				ave += slipRate[i];
			int index = seg - (numPts + 1) / 2;
			smoothSlipRate[index] = ave / numPts;
		}

		for (int seg = 0; seg < n_seg; seg++)
			subSectionList.get(seg).setAveLongTermSlipRate(smoothSlipRate[seg]);

		// plot orig and final slip rates
		double min = 0, max = n_seg - 1;
		EvenlyDiscretizedFunc origSlipRateFunc = new EvenlyDiscretizedFunc(min,
				max, n_seg);
		EvenlyDiscretizedFunc finalSlipRateFunc = new EvenlyDiscretizedFunc(
				min, max, n_seg);
		for (int seg = 0; seg < n_seg; seg++) {
			origSlipRateFunc.set(seg, slipRate[seg]);
			finalSlipRateFunc.set(seg, smoothSlipRate[seg]);
		}
		ArrayList sr_funcs = new ArrayList();
		origSlipRateFunc.setName("Orig Slip Rates");
		finalSlipRateFunc.setName("Smooth Slip Rates");
		sr_funcs.add(origSlipRateFunc);
		sr_funcs.add(finalSlipRateFunc);
		GraphiWindowAPI_Impl sr_graph = new GraphiWindowAPI_Impl(sr_funcs,
				"Orig Versus Smoothed Slip Rates");

	}

	/**
	 * Get a list of all subsections
	 * 
	 * @return
	 */
	public ArrayList<FaultSectionPrefData> getAllSubsections() {
		return this.subSectionList;
	}

	private final int[][] getRupInSegMatrix(int num_seg) {

		int num_rup, nSegInRup, n_rup_wNseg;
		if (numSegForSmallestRups == 1) {
			num_rup = num_seg * (num_seg + 1) / 2;
			nSegInRup = 1; // the number of segments in rupture (initialized as
							// 1)
			n_rup_wNseg = num_seg; // the number of ruptures with the above N
									// segments
		} else { // numSegForSmallestRups == 2
			num_rup = num_seg * (num_seg + 1) / 2 - num_seg;
			nSegInRup = 2; // the number of segments in rupture (initialized as
							// 1)
			n_rup_wNseg = num_seg - 1; // the number of ruptures with the above
										// N segments
		}

		numSegInRup = new int[num_rup];
		firstSegOfRup = new int[num_rup];

		int remain_rups = n_rup_wNseg;
		int startSeg = 0;
		int[][] rupInSeg = new int[num_seg][num_rup];
		for (int rup = 0; rup < num_rup; rup += 1) {
			numSegInRup[rup] = nSegInRup;
			firstSegOfRup[rup] = startSeg;
			for (int seg = startSeg; seg < startSeg + nSegInRup; seg += 1)
				rupInSeg[seg][rup] = 1;
			startSeg += 1;
			remain_rups -= 1;
			if (remain_rups == 0) {
				startSeg = 0;
				nSegInRup += 1;
				n_rup_wNseg -= 1;
				remain_rups = n_rup_wNseg;
			}
		}

		// check result
		/*
		 * try{ FileWriter fw = new FileWriter("TestRupInSegMatrix.txt");
		 * BufferedWriter br = new BufferedWriter(fw); String line; for(int rup =
		 * 0; rup < num_rup; rup += 1) { line = new String("\n"); for(int seg =
		 * 0; seg < num_seg; seg+=1) line += rupInSeg[seg][rup]+"\t";
		 * br.write(line); } br.close(); }catch(Exception e){
		 * e.printStackTrace(); }
		 */

		/*
		 * if(D) { for(int seg = 0; seg < num_seg; seg+=1) {
		 * System.out.print("\n"); for(int rup = 0; rup < num_rup; rup += 1)
		 * System.out.print(rupInSeg[seg][rup]+" "); } System.out.print("\n"); }
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
		totMoRate = 0;
		double aveSegDDW = 0, aveSegLength = 0;

		for (int seg = 0; seg < num_seg; seg++) {
			segData = subSectionList.get(seg);
			segArea[seg] = segData.getDownDipWidth() * segData.getLength()
					* 1e6 * (1.0 - segData.getAseismicSlipFactor()); // km
																		// --> m
			segSlipRate[seg] = segData.getAveLongTermSlipRate() * 1e-3; // mm/yr
																		// -->
																		// m/yr
			segSlipRateStdDev[seg] = segData.getSlipRateStdDev() * 1e-3; // mm/yr
																			// -->
																			// m/yr
			segMoRate[seg] = FaultMomentCalc.getMoment(segArea[seg],
					segSlipRate[seg]); // 
			totMoRate += segMoRate[seg];
			aveSegDDW += segData.getDownDipWidth();
			aveSegLength += segData.getLength();

			// keep min and max length and area
			if (segData.getLength() < minLength)
				minLength = segData.getLength();
			if (segData.getLength() > maxLength)
				maxLength = segData.getLength();
			if (segArea[seg] / 1e6 < minArea)
				minArea = segArea[seg] / 1e6;
			if (segArea[seg] / 1e6 > maxArea)
				maxArea = segArea[seg] / 1e6;
		}
		aveSegDDW /= num_seg;
		aveSegLength /= num_seg;

		// if(D)
		// System.out.println("minSegArea="+(float)minArea+"\nmaxSegArea="+(float)maxArea+"\nminSegLength="+(float)minLength+"\nmaxSegLength="+(float)maxLength);
		if (D)
			System.out.println("nminSegLength=" + (float) minLength
					+ "\tmaxSegLength=" + (float) maxLength);

		System.out
				.print("\nAverage DDW & Length of sub-sections, and implied mag of "
						+ numSegForSmallestRups + " of these rupturing: ");
		double mag = this.magAreaRel.getMedianMag(numSegForSmallestRups
				* aveSegDDW * aveSegLength);
		// round and save this for the GR constraint
		smallestGR_constriantMag = ((double) Math.round(mag * 10.0)) / 10.0;
		System.out.println((float) aveSegDDW + "\t" + (float) aveSegLength
				+ "\t" + (float) mag + "\t" + smallestGR_constriantMag + "\n");

		// compute rupture areas
		for (int rup = 0; rup < num_rup; rup++) {
			rupArea[rup] = 0;
			for (int seg = 0; seg < num_seg; seg++)
				if (rupInSeg[seg][rup] == 1)
					rupArea[rup] += segArea[seg];
		}
	}

	/**
	 * This creates the segSlipInRup (Dsr) matrix based on the value of
	 * slipModelType. This slips are in meters.
	 * 
	 */
	private void computeSegSlipInRupMatrix() {
		segSlipInRup = new double[num_seg][num_rup];
		FaultSectionPrefData segData;

		// for case segment slip is independent of rupture (constant), and equal
		// to slip-rate * MRI
		if (slipModelType.equals(CHAR_SLIP_MODEL)) {
			throw new RuntimeException(CHAR_SLIP_MODEL + " not yet supported");
		}
		// for case where ave slip computed from mag & area, and is same on all
		// segments
		else if (slipModelType.equals(UNIFORM_SLIP_MODEL)) {
			for (int rup = 0; rup < num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]
						/ (rupArea[rup] * FaultMomentCalc.SHEAR_MODULUS); // inlcudes
																			// aveSlipCorr
				for (int seg = 0; seg < num_seg; seg++) {
					segSlipInRup[seg][rup] = rupInSeg[seg][rup] * aveSlip;
				}
			}
		}
		// this is the model where seg slip is proportional to segment slip rate
		// (bumped up or down based on ratio of seg slip rate over wt-ave slip
		// rate (where wts are seg areas)
		else if (slipModelType.equals(WG02_SLIP_MODEL)) {
			for (int rup = 0; rup < num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]
						/ (rupArea[rup] * FaultMomentCalc.SHEAR_MODULUS); // inlcudes
																			// aveSlipCorr
				double totMoRate = 0; // a proxi for slip-rate times area
				double totArea = 0;
				for (int seg = 0; seg < num_seg; seg++) {
					if (rupInSeg[seg][rup] == 1) {
						totMoRate += segMoRate[seg]; // a proxi for Vs*As
						totArea += segArea[seg];
					}
				}
				for (int seg = 0; seg < num_seg; seg++) {
					segSlipInRup[seg][rup] = aveSlip * rupInSeg[seg][rup]
							* segMoRate[seg] * totArea
							/ (totMoRate * segArea[seg]);
				}
			}
		} else if (slipModelType.equals(TAPERED_SLIP_MODEL)) {
			// note that the ave slip is partitioned by area, not length; this
			// is so the final model is moment balanced.
			mkTaperedSlipFuncs();
			for (int rup = 0; rup < num_rup; ++rup) {
				double aveSlip = rupMeanMo[rup]
						/ (rupArea[rup] * FaultMomentCalc.SHEAR_MODULUS); // inlcudes
																			// aveSlipCorr
				// System.out.println(rup+"\t"+(float)aveSlip+" m");
				double normBegin = 0, normEnd, scaleFactor;
				for (int seg = 0; seg < num_seg; seg++) {
					if (rupInSeg[seg][rup] == 1) {
						normEnd = normBegin + segArea[seg] / rupArea[rup];
						// normEnd = normBegin + 1.0/(double)numSegInRup[rup];
						// fix normEnd values that are just past 1.0
						if (normEnd > 1 && normEnd < 1.00001)
							normEnd = 1.0;
						scaleFactor = taperedSlipCDF.getInterpolatedY(normEnd)
								- taperedSlipCDF.getInterpolatedY(normBegin);
						scaleFactor /= (normEnd - normBegin);
						segSlipInRup[seg][rup] = aveSlip * scaleFactor;
						normBegin = normEnd;
					}
				}
				/*
				 * if(rup == num_rup-1) { // check results double d_aveTest=0;
				 * for(int seg=0; seg<num_seg; seg++) d_aveTest +=
				 * segSlipInRup[seg][rup]*segArea[seg]/rupArea[rup];
				 * System.out.println("AveSlipCheck: " + (float)
				 * (d_aveTest/aveSlip)); }
				 */
			}
		} else
			throw new RuntimeException("slip model not supported");

		// for(int seg=0; seg<num_seg; seg++)
		// System.out.println(seg+"\t"+segSlipInRup[seg][num_rup-1]);

	}

	/**
	 * This makes a tapered slip function based on the [Sin(x)]^0.5 fit of Biasi &
	 * Weldon (in prep; pesonal communication), which is based on the data
	 * comilation of Biasi & Weldon (2006, "Estimating Surface Rupture Length
	 * and Magnitude of Paleoearthquakes from Point Measurements of Rupture
	 * Displacement", Bull. Seism. Soc. Am. 96, 1612-1623, doi:
	 * 10.1785/0120040172 E)
	 * 
	 */
	private static void mkTaperedSlipFuncs() {

		// only do if another instance has not already done this
		if (taperedSlipCDF != null)
			return;

		taperedSlipCDF = new EvenlyDiscretizedFunc(0, 5001, 0.0002);
		taperedSlipPDF = new EvenlyDiscretizedFunc(0, 5001, 0.0002);
		double x, y, sum = 0;
		int num = taperedSlipPDF.getNum();
		for (int i = 0; i < num; i++) {
			x = taperedSlipPDF.getX(i);
			// y = Math.sqrt(1-(x-0.5)*(x-0.5)/0.25);
			y = Math.pow(Math.sin(x * Math.PI), 0.5);
			taperedSlipPDF.set(i, y);
			sum += y;
		}

		// now make final PDF & CDF
		y = 0;
		for (int i = 0; i < num; i++) {
			y += taperedSlipPDF.getY(i);
			taperedSlipCDF.set(i, y / sum);
			taperedSlipPDF.set(i, taperedSlipPDF.getY(i) / sum);
			// System.out.println(taperedSlipCDF.getX(i)+"\t"+taperedSlipPDF.getY(i)+"\t"+taperedSlipCDF.getY(i));
		}
	}

	/**
	 * This computes the total event rate prediction error (ignoring wt given to
	 * this equation set), meaning it will give a result even if the equation
	 * set wt was zero.
	 * 
	 * @return
	 */
	private double getTotEventRatePredErr() {
		SegRateConstraint constraint;
		double totPredErr = 0;
		for (int i = 0; i < segRateConstraints.size(); i++) {
			constraint = segRateConstraints.get(i);
			int seg = constraint.getSegIndex();
			double normResid = (finalPaleoVisibleSegEventRate[seg] - constraint
					.getMean())
					/ constraint.getStdDevOfMean();
			totPredErr += normResid * normResid;
		}
		return totPredErr;
	}

	/**
	 * This gets the rupture rate smoothness prediction error regardless of whether it was
	 * used in the inversion
	 * 
	 * @return
	 */
	private double getTotSmoothnessPredErr() {
		double predErr = 0;
		for (int rup = 0; rup < num_rup; rup++) {
			// check to see if the last segment is used by the rupture (skip
			// this last rupture if so)
			if (rupInSeg[num_seg - 1][rup] != 1) {
				predErr += (rupRateSolution[rup] - rupRateSolution[rup + 1])
						* (rupRateSolution[rup] - rupRateSolution[rup + 1]);
			}
		}
		return predErr;
	}
	
	
	/**
	 * This gets the slip rate smoothness prediction error regardless of whether it was
	 * used in the inversion
	 * 
	 * @return
	 */
	private double getTotSlipRateSmoothnessPredErr() {
		double predErr = 0;
		double temp;
		for (int row = 0; row < num_seg; row++) {
			temp=0;
			for (int col = 0; col < num_rup-1; col++) {
				temp += segSlipInRup[row][col] * rupRateSolution[col]
				     - segSlipInRup[row][col] * rupRateSolution[col+1];
			}
			predErr += temp * temp;
			
		}
		return predErr;
	}
	

	// This gets the seg-rate constraints by associating locations from Appendix
	// C to those sub-sections created here
	private void getPaleoSegRateConstraints() {
		segRateConstraints = new ArrayList<SegRateConstraint>();
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass()
					.getClassLoader().getResourceAsStream(SEG_RATE_FILE_NAME));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet sheet = wb.getSheetAt(0);
			int lastRowIndex = sheet.getLastRowNum();
			double lat, lon, rate, sigma, lower95Conf, upper95Conf;
			String siteName;
			for (int r = 1; r <= lastRowIndex; ++r) {

				// read the event from the file
				HSSFRow row = sheet.getRow(r);
				if (row == null)
					continue;
				HSSFCell cell = row.getCell((short) 1);
				if (cell == null
						|| cell.getCellType() == HSSFCell.CELL_TYPE_STRING)
					continue;
				lat = cell.getNumericCellValue();
				siteName = row.getCell((short) 0).getStringCellValue().trim();
				lon = row.getCell((short) 2).getNumericCellValue();
				rate = row.getCell((short) 3).getNumericCellValue();
				sigma = row.getCell((short) 4).getNumericCellValue();
				lower95Conf = row.getCell((short) 7).getNumericCellValue();
				upper95Conf = row.getCell((short) 8).getNumericCellValue();

				// get Closest sub section
				double minDist = Double.MAX_VALUE, dist;
				int closestFaultSectionIndex = -1;
				Location loc = new Location(lat, lon);
				for (int sectionIndex = 0; sectionIndex < subSectionList.size(); ++sectionIndex) {
					dist = subSectionList.get(sectionIndex).getFaultTrace()
							.minDistToLine(loc);
					if (dist < minDist) {
						minDist = dist;
						closestFaultSectionIndex = sectionIndex;
					}
				}
				if (minDist > 2)
					continue; // closest fault section is at a distance of
								// more than 2 km

				// add to Seg Rate Constraint list
				String name = subSectionList.get(closestFaultSectionIndex)
						.getSectionName()
						+ " --" + siteName;
				SegRateConstraint segRateConstraint = new SegRateConstraint(
						name);
				segRateConstraint.setSegRate(closestFaultSectionIndex, rate,
						sigma, lower95Conf, upper95Conf);
				// System.out.println(name+"\t"+closestFaultSectionIndex+"\t"+rate+"\t"+sigma+"\t"+lower95Conf+"\t"+upper95Conf);
				segRateConstraints.add(segRateConstraint);
			}
		} catch (Exception e) {
			e.printStackTrace();
		}

	}

	private int getParkfieldRuptureIndex() {
		int num = numSubSections[0];
		int target = -1;
		for (int r = 0; r < num_rup; r++)
			if (rupInSeg[0][r] == 1 && rupInSeg[num - 1][r] == 1
					&& rupInSeg[num][r] == 0) {
				target = r;
				break;
			}
		return target;
	}

	/**
	 * This constrains the rate of the parkfield event to be the observed rate,
	 * plus any events smaller than parkfield to have zero rate
	 */
	private void setAprioriRupRates() {

		double parkfieldMag = rupMeanMag[getParkfieldRuptureIndex()];

		int numMagsBelowParkfield = 0;
		for (int r = 0; r < num_rup; r++)
			if (rupMeanMag[r] < parkfieldMag) {
				numMagsBelowParkfield += 1;
				// System.out.println(r+"\t"+rupMeanMag[r]);
			}

		int num_constraints = numMagsBelowParkfield + 1; // add one for the
															// parkfield rupture
															// itself
		// int num_constraints = numMagsBelowParkfield;
		aPriori_rupIndex = new int[num_constraints];
		aPriori_rate = new double[num_constraints];
		aPriori_wt = new double[num_constraints];

		// set the zero constraints
		int counter = 0;
		for (int r = 0; r < num_rup; r++)
			if (rupMeanMag[r] < parkfieldMag) {
				aPriori_rupIndex[counter] = r;
				aPriori_rate[counter] = 0.0;
				aPriori_wt[counter] = 1;
				counter += 1;
			}

		/*	*/
		// Set parkfield rate to ~25 years
		aPriori_rupIndex[num_constraints - 1] = getParkfieldRuptureIndex();
		aPriori_rate[num_constraints - 1] = PARKFIELD_EVENT_RATE;
		aPriori_wt[num_constraints - 1] = 1;

	}

	/**
	 * This gets the non-negative least squares solution for the matrix C and
	 * data vector d.
	 * 
	 * @param C
	 * @param d
	 * @return
	 */

	private static double[] getNNLS_solution(double[][] C, double[] d) {

		int nRow = C.length;
		int nCol = C[0].length;

		double[] A = new double[nRow * nCol];
		double[] x = new double[nCol];

		int i, j, k = 0;

		if (MATLAB_TEST) {
			System.out.println("display " + "SSAF Inversion test");
			System.out.println("C = [");
			for (i = 0; i < nRow; i++) {
				for (j = 0; j < nCol; j++)
					System.out.print(C[i][j] + "   ");
				System.out.print("\n");
			}
			System.out.println("];");
			System.out.println("d = [");
			for (i = 0; i < nRow; i++)
				System.out.println(d[i]);
			System.out.println("];");
		}
		// ///////////////////////////////////

		for (j = 0; j < nCol; j++)
			for (i = 0; i < nRow; i++) {
				A[k] = C[i][j];
				k += 1;
			}
		nnls.update(A, nRow, nCol);

		boolean converged = nnls.solve(d, x);
		if (!converged)
			throw new RuntimeException("ERROR:  NNLS Inversion Failed");

		if (MATLAB_TEST) {
			System.out.println("x = [");
			for (i = 0; i < x.length; i++)
				System.out.println(x[i]);
			System.out.println("];");
			System.out.println("max(abs(x-lsqnonneg(C,d)))");
		}

		return x;
	}

	private static double[] getSimulatedAnnealing_solution(double[][] A,
			double[] d) {

		int nRow = A.length;
		int nCol = A[0].length;

		System.out.println("nRow = " + nRow);
		System.out.println("nCol = " + nCol);
		
		double[] x = new double[nCol]; // current model
		double[] xbest = new double[nCol]; // best model seen so far
		double[] xnew = new double[nCol]; // new perturbed model
		double[] initial_state = new double[nCol]; // starting model
		double[] perturb = new double[nCol]; // perturbation to current model
		double[] syn = new double[nRow]; // data synthetics
		double[] misfit = new double[nRow]; // mifit between data and synthetics

		double E, Enew, Ebest, T, P, r;
		int i, j, iter, numiter, index;

		//Random r = new Random(System.currentTimeMillis());
		
		// Set initial state (random or a priori starting model)
		for (i = 0; i < nCol; i++) {
			initial_state[i] = 0; // Need to Change !!!
		//	initial_state[i] = Math.random() / 100000;
		}
		for (j = 0; j < nCol; j++) {
			x[j] = initial_state[j];
		}
		// x=initial_state.clone();
		
		// Initial "best" solution & its Energy
		for (j = 0; j < nCol; j++) {
			xbest[j] = x[j];  
		}
		
		E = 0;
		for (i = 0; i < nRow; i++) {
			syn[i] = 0;
			for (j = 0; j < nCol; j++) {
				syn[i] += A[i][j] * x[j]; // compute predicted data
			}
			misfit[i] = syn[i] - d[i];  // misfit between synthetics and data
			E += Math.pow(misfit[i], 2);  // L2 norm of misfit vector
		}
		//E = Math.sqrt(E);
		Ebest = E;
		System.out.println("Starting energy = " + Ebest);
		
		numiter = 100000;
		for (iter = 1; iter <= numiter; iter++) {
			
			
			// Simulated annealing "temperature"
			// T = 1 / (double) iter; 
			// T = 1/Math.log( (double) iter);
			// T = Math.pow(0.999,iter-1);
			T = Math.exp(-( (double) iter - 1));
			
			if ((double) iter / 10000 == Math.floor(iter / 10000)) {
				System.out.println("Iteration # " + iter);
			//	System.out.println("T = " + T);
				System.out.println("Lowest energy found = " + Ebest);
			}
					
			
			// Pick neighbor of current model
			for (j = 0; j < nCol; j++) {
				xnew[j]=x[j];
			}
			
			// Index of model to randomly perturb
			index = (int) Math.floor(Math.random() * nCol); 
			
			// How much to perturb index (can be a function of T)	
			perturb[index] = (Math.random()-0.5) * 0.001;
			// perturb[index] =  (1/Math.sqrt(T)) * r.nextGaussian() * 0.0001 * Math.exp(1/(2*T)); 
			// perturb[index] = T * 0.001 * Math.tan(Math.PI*Math.random() - Math.PI/2);		
			// r = Math.random();
			// perturb[index] = Math.signum(r-0.5) * T * 0.001 * (Math.pow(1+1/T,Math.abs(2*r-1))-1);
			
			// Nonnegativity constraint
			// while (x[index] + perturb[index] < 0) {
			// perturb[index] = (Math.random()-0.5)*0.001;
			// }		
			if (xnew[index] + perturb[index] < 0) {
				perturb[index] = -xnew[index];
			}
			xnew[index] += perturb[index];
			
			// Calculate "energy" of new model (high misfit -> high energy)
			Enew = 0;
			for (i = 0; i < nRow; i++) {
				syn[i] = 0;
				for (j = 0; j < nCol; j++) {
					syn[i] += A[i][j] * xnew[j]; // compute predicted data
				}
				misfit[i] = syn[i] - d[i];  // misfit between synthetics and data
				Enew += Math.pow(misfit[i], 2);  // L2 norm of misfit vector
			}
			//Enew = Math.sqrt(Enew);
			
			// Is this a new best?
			if (Enew < Ebest) {
				for (j = 0; j < nCol; j++) {
					xbest[j] = xnew[j]; }
				Ebest = Enew;
			}

			// Change state? Calculate transition probability P
			if (Enew < E) {
				P = 1; // Always keep new model if better
			} else {
			
				// Sometimes keep new model if worse (depends on T)
				P = Math.exp((E - Enew) / (double) T); 
			}
			
			if (P > Math.random()) {
				for (j = 0; j < nCol; j++) {
					x[j]=xnew[j];
				}
				E = Enew;
				//System.out.println("New soluton kept! E = " + E + ". P = " + P);
				
			}
			
		}

		// Preferred model is best model seen during annealing process
		return xbest;
	}

	/**
	 * Computer Final Slip Rate for each segment (& aPrioriSegSlipRate)
	 * 
	 */
	private void computeFinalStuff() {

		// compute segment slip and event rates
		finalSegSlipRate = new double[num_seg];
		finalSegEventRate = new double[num_seg];
		finalPaleoVisibleSegEventRate = new double[num_seg];
		for (int seg = 0; seg < num_seg; seg++) {
			finalSegSlipRate[seg] = 0;
			finalSegEventRate[seg] = 0;
			for (int rup = 0; rup < num_rup; rup++)
				if (rupInSeg[seg][rup] == 1) {
					finalSegSlipRate[seg] += rupRateSolution[rup]
							* segSlipInRup[seg][rup];
					finalSegEventRate[seg] += rupRateSolution[rup];
					finalPaleoVisibleSegEventRate[seg] += rupRateSolution[rup]
							* getProbVisible(rupMeanMag[rup]);
				}
			// System.out.println((float)(finalSegSlipRate[seg]/this.d_pred[seg]));
			// double absFractDiff =
			// Math.abs(finalSegSlipRate[seg]/(segSlipRate[seg]*(1-this.moRateReduction))
			// - 1.0);
		}

		// Compute the total Mag Freq Dist
		magFreqDist = new SummedMagFreqDist(5, 41, 0.1);
		meanMagHistorgram = new SummedMagFreqDist(4, 51, 0.1);
		magHistorgram = new SummedMagFreqDist(4, 51, 0.1);
		for (int rup = 0; rup < num_rup; rup++) {
			// add MFD of this rupture
			GaussianMagFreqDist gDist = new GaussianMagFreqDist(5.0, 9.0, 41,
					rupMeanMag[rup], GAUSS_MFD_SIGMA, 1.0,
					GAUSS_MFD_TRUNCATION, 2); // dist w/ unit moment rate
			gDist.scaleToCumRate(0, rupRateSolution[rup]);
			magFreqDist.addIncrementalMagFreqDist(gDist);

			// add to mag historgrams
			meanMagHistorgram.add(rupMeanMag[rup], 1.0);
			gDist = new GaussianMagFreqDist(4.0, 9.0, 51, rupMeanMag[rup],
					GAUSS_MFD_SIGMA, 1.0, GAUSS_MFD_TRUNCATION, 2);
			gDist.scaleToCumRate(0, 1.0); // this makes it a PDF
			magHistorgram.addIncrementalMagFreqDist(gDist);
		}
		magFreqDist.setInfo("Incremental Mag Freq Dist");
		meanMagHistorgram.setInfo("Mean Mag Histogram");
		magHistorgram
				.setInfo("Mag Historgram (including aleatory variability)");

		// System.out.println("\nTEST MFD\n"+testMagFreqDist.toString()+"\n");

		// for(int i=0; i<testMagFreqDist.getNum()-1; i++)
		// System.out.println(testMagFreqDist.getX(i)+"-"+testMagFreqDist.getX(i+1)+"\t"+
		// (testMagFreqDist.getY(i)-testMagFreqDist.getY(i+1)));

		// check moment rate
		double origMoRate = totMoRate * (1 - moRateReduction);
		double ratio = origMoRate / magFreqDist.getTotalMomentRate();
		System.out
				.println("Moment Rates: from Fault Sections (possible reduced) = "
						+ (float) origMoRate
						+ ";  from total MFD = "
						+ (float) magFreqDist.getTotalMomentRate()
						+ ",  ratio = " + (float) ratio + "\n");

		// COMPUTE RATE AT WHICH SECTION BOUNDARIES CONSTITUTE RUPTURE ENDPOINTS
		rateOfRupEndsOnSeg = new double[num_seg + 1]; // there is one more
														// boundary than
														// segments
		for (int rup = 0; rup < num_rup; rup++) {
			int beginBoundary = firstSegOfRup[rup];
			int endBoundary = firstSegOfRup[rup] + numSegInRup[rup];
			rateOfRupEndsOnSeg[beginBoundary] += rupRateSolution[rup];
			rateOfRupEndsOnSeg[endBoundary] += rupRateSolution[rup];
		}

	}

	/**
	 * This computes both participation and nucleation MFDs for each sub-section
	 */
	private void computeSegMFDs() {
		segmentNucleationMFDs = new ArrayList<SummedMagFreqDist>();
		segmentParticipationMFDs = new ArrayList<SummedMagFreqDist>();
		SummedMagFreqDist sumOfSegNuclMFDs = new SummedMagFreqDist(5, 41, 0.1);
		SummedMagFreqDist sumOfSegPartMFDs = new SummedMagFreqDist(5, 41, 0.1);
		aveOfSegPartMFDs = new SummedMagFreqDist(5, 41, 0.1);

		SummedMagFreqDist segPartMFD, segNuclMFD;
		// double mag, rate;
		for (int seg = 0; seg < num_seg; seg++) {
			segPartMFD = new SummedMagFreqDist(5, 41, 0.1);
			segNuclMFD = new SummedMagFreqDist(5, 41, 0.1);
			for (int rup = 0; rup < num_rup; rup++) {
				if (this.rupInSeg[seg][rup] == 1) {
					// mag = this.rupMeanMag[rup];
					// rate = rupRateSolution[rup];
					// segNuclMFD.addResampledMagRate(mag,
					// rate/numSegInRup[rup], false); // uniform probability
					// that any sub-section will nucleate
					// segPartMFD.addResampledMagRate(mag, rate, false);
					if (rupRateSolution[rup] > 0) {
						GaussianMagFreqDist mfd = new GaussianMagFreqDist(5.0,
								9.0, 41, rupMeanMag[rup], GAUSS_MFD_SIGMA, 1.0,
								GAUSS_MFD_TRUNCATION, 2); // dist w/ unit
															// moment rate
						mfd.scaleToCumRate(0, rupRateSolution[rup]);
						segPartMFD.addIncrementalMagFreqDist(mfd);
						mfd.scaleToCumRate(0, rupRateSolution[rup]
								/ numSegInRup[rup]);
						segNuclMFD.addIncrementalMagFreqDist(mfd);
					}
				}
			}
			segmentNucleationMFDs.add(segNuclMFD);
			segmentParticipationMFDs.add(segPartMFD);
			sumOfSegNuclMFDs.addIncrementalMagFreqDist(segNuclMFD);
			sumOfSegPartMFDs.addIncrementalMagFreqDist(segPartMFD);
		}
		// compute aveOfSegPartMFDs from sumOfSegPartMFDs
		for (int m = 0; m < sumOfSegPartMFDs.getNum(); m++)
			aveOfSegPartMFDs.add(m, sumOfSegPartMFDs.getY(m) / num_seg);
		aveOfSegPartMFDs.setInfo("Average Seg Participation MFD");

		// test the sum of segmentNucleationMFDs (checks out for both 5 and 10
		// km subsection lengths)
		/*
		 * System.out.println("TEST SUMMED MFDs"); for(int m=0; m<sumOfSegNuclMFDs.getNum();m++)
		 * System.out.println(m+"\t"+sumOfSegNuclMFDs.getX(m)+"\t"+(float)sumOfSegNuclMFDs.getY(m)+
		 * "\t"+(float)magFreqDist.getY(m)+"\t"+
		 * (float)(sumOfSegNuclMFDs.getY(m)/magFreqDist.getY(m)));
		 */
	}

	public void writeFinalStuff() {

		// write out rupture rates and mags
		// System.out.println("Final Rupture Rates & Mags:");
		// for(int rup=0; rup < num_rup; rup++)
		// System.out.println(rup+"\t"+(float)rupRateSolution[rup]+"\t"+(float)rupMeanMag[rup]);

		// WRITE OUT MAXIMUM EVENT RATE & INDEX
		double maxRate = 0;
		int index = -1;
		for (int seg = 0; seg < num_seg; seg++)
			if (finalSegEventRate[seg] > maxRate) {
				maxRate = finalSegEventRate[seg];
				index = seg;
			}
		int mri = (int) Math.round(1.0 / maxRate);
		System.out.println("\nMax seg rate (MRI): " + (float) maxRate + " ("
				+ mri + " yrs) at index " + index);

		// WRITE OUT PARKFIED INFO
		index = getParkfieldRuptureIndex();
		mri = (int) Math.round(1.0 / rupRateSolution[index]);
		System.out.println("\nParkfield:\trup index = " + index + "; mag = "
				+ (float) rupMeanMag[index] + "; rate = "
				+ (float) rupRateSolution[index] + " (" + mri + ")");
		double aveSegRate = 0;
		int numSubSect = numSubSections[0];
		for (int seg = 0; seg < numSubSect; seg++)
			aveSegRate += finalSegEventRate[seg];
		aveSegRate /= numSubSect;
		mri = (int) Math.round(1.0 / aveSegRate);
		System.out.println("\t\tave rate (MRI) of the " + numSubSect
				+ " sub-sections =" + (float) aveSegRate + " (" + mri + ")");

		// write out number of ruptures that have rates above minRupRate
		int numAbove = 0;
		for (int rup = 0; rup < this.rupRateSolution.length; rup++)
			if (rupRateSolution[rup] > minRupRate)
				numAbove += 1;
		System.out.println("\nNum Ruptures above minRupRate = " + numAbove
				+ "\t(out of " + rupRateSolution.length + ")\n");

		// write out final segment slip rates
		// System.out.println("\nSegment Slip Rates: index, final, orig, and
		// final/orig (orig is corrected for moRateReduction)");
		double aveRatio = 0;
		for (int seg = 0; seg < num_seg; seg++) {
			double slipRate = segSlipRate[seg] * (1 - this.moRateReduction);
			aveRatio += finalSegSlipRate[seg] / slipRate;
			// System.out.println(seg+"\t"+(float)finalSegSlipRate[seg]+"\t"+(float)slipRate+"\t"+(float)(finalSegSlipRate[seg]/slipRate));
		}
		aveRatio /= num_seg;
		System.out.println("Ave final/orig slip rate = " + (float) aveRatio);

		// write out final segment event rates
		if (relativeSegRateWt > 0.0) {
			// System.out.println("\nSegment Rates: index, final, orig, and
			// final/orig");
			aveRatio = 0;
			SegRateConstraint constraint;
			for (int i = 0; i < segRateConstraints.size(); i++) {
				int row = firstRowSegEventRateData + i;
				constraint = segRateConstraints.get(i);
				int seg = constraint.getSegIndex();
				// this checks that finalSegEventRate[seg] and d_pred[row} are
				// the same (RECONSIDER PROB VISIBLE IF I USE THIS AGAIN)
				// System.out.println(seg+"\t"+(float)finalSegEventRate[seg]+"\t"+(float)d_pred[row]+"\t"+(float)(finalSegEventRate[seg]/d_pred[row]));
				if (applyProbVisible) {
					aveRatio += finalPaleoVisibleSegEventRate[seg]
							/ constraint.getMean();
					// System.out.println(seg+"\t"+(float)finalPaleoReducedSegEventRate[seg]+"\t"+(float)constraint.getMean()+"\t"+(float)aveRatio);
				} else {
					aveRatio += finalSegEventRate[seg] / constraint.getMean();
					// System.out.println(seg+"\t"+(float)finalSegEventRate[seg]+"\t"+(float)constraint.getMean()+"\t"+(float)aveRatio);
				}
			}
			aveRatio /= segRateConstraints.size();
			System.out.println("Ave final/orig segment rate = "
					+ (float) aveRatio);
		}

		// write out final rates for ruptures with an a-priori constraint
		if (this.relative_aPrioriRupWt > 0.0)
			aveRatio = 0;
		// System.out.println("\nA Priori Rates: index, final, orig, and
		// final/orig");
		for (int i = 0; i < this.aPriori_rate.length; i++) {
			double ratio;
			if (rupRateSolution[aPriori_rupIndex[i]] > 1e-14
					&& aPriori_rate[i] > 1e-14) // if both are not essentially
												// zero
				ratio = (rupRateSolution[aPriori_rupIndex[i]] / aPriori_rate[i]);
			else
				ratio = 1;
			aveRatio += ratio;
			// System.out.println(aPriori_rupIndex[i]+"\t"+(float)rupRateSolution[aPriori_rupIndex[i]]+"\t"+aPriori_rate[i]+"\t"+(float)ratio);
		}
		aveRatio /= aPriori_rate.length;
		System.out
				.println("Ave final/orig a-priori rate = " + (float) aveRatio);

	}

	public void writePredErrorInfo() {

		// First without equation weights
		double totPredErr = 0, slipRateErr = 0, eventRateErr = 0, aPrioriErr = 0, smoothnessErr = 0, SlipRateSmoothnessErr = 0, grErr = 0, parkSegRateErr = 0;

		for (int row = firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row++)
			slipRateErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
					* data_wt[row] * data_wt[row];
		if (relativeSegRateWt > 0)
			for (int row = firstRowSegEventRateData; row <= lastRowSegEventRateData; row++)
				eventRateErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
						* data_wt[row] * data_wt[row];
		if (relative_aPrioriRupWt > 0)
			for (int row = firstRowAprioriData; row <= lastRowAprioriData; row++)
				aPrioriErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
						* data_wt[row] * data_wt[row];
		if (relative_smoothnessWt > 0)
			for (int row = firstRowSmoothnessData; row <= lastRowSmoothnessData; row++)
				smoothnessErr += (d[row] - d_pred[row])
						* (d[row] - d_pred[row]) * data_wt[row] * data_wt[row];
		if (relativeSlipRateSmoothnessWt > 0)
			for (int row = firstRowSlipRateSmoothnessData; row <= lastRowSlipRateSmoothnessData; row++)
				SlipRateSmoothnessErr += (d[row] - d_pred[row])
						* (d[row] - d_pred[row]) * data_wt[row] * data_wt[row];
		if (relativeGR_constraintWt > 0)
			for (int row = firstRowGR_constraintData; row <= lastRowGR_constraintData; row++) {
				grErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
						* data_wt[row] * data_wt[row];
				// double err =
				// (d[row]-d_pred[row])*(d[row]-d_pred[row])*data_wt[row]*data_wt[row];
				// System.out.println(row+"\t"+(float)d_pred[row]);
			}
		if (relative_aPrioriSegRateWt > 0)
			for (int row = firstRowParkSegConstraint; row <= lastRowParkSegConstraint; row++)
				parkSegRateErr += (d[row] - d_pred[row])
						* (d[row] - d_pred[row]) * data_wt[row] * data_wt[row];
		totPredErr = slipRateErr + eventRateErr + aPrioriErr + smoothnessErr + SlipRateSmoothnessErr
				+ grErr + parkSegRateErr;

		// get alt versions in case equation wts zero
		double eventRateErrAlt = getTotEventRatePredErr();
		double smoothnessErrAlt = getTotSmoothnessPredErr();
		double SlipRateSmoothnessErrAlt = getTotSlipRateSmoothnessPredErr();
		
		double aveSRnormResid = Math.sqrt(slipRateErr / num_seg);
		double aveERnormResid = Math.sqrt(eventRateErrAlt
				/ segRateConstraints.size());

		String resultsString = "\nTotal Prediction Error =\t\t"
				+ (float) totPredErr + "\n\t" + "Slip Rate Err =\t\t\t"
				+ (float) slipRateErr + "\trel. wt = 1.0"
				+ "\tnorm resid rms = " + (float) aveSRnormResid + "\n\t"
				+ "Event Rate Err =\t\t" + (float) eventRateErrAlt
				+ "\trel. wt = " + relativeSegRateWt + "\tnorm resid rms = "
				+ (float) aveERnormResid + "\n\t" + "A Priori Err =\t\t\t"
				+ (float) aPrioriErr + "\trel. wt = " + relative_aPrioriRupWt
				+ "\n\t" + "Smoothness Err =\t\t" + (float) smoothnessErrAlt		
				+ "\trel. wt = " + relative_smoothnessWt + "\n\t"		
				+ "Slip Rate Smoothing Err =\t" + (float) SlipRateSmoothnessErrAlt		
				+ "\trel. wt = " + relativeSlipRateSmoothnessWt + "\n\t"		
				+ "GR Err =\t\t\t" + (float) grErr + "\trel. wt = "
				+ relativeGR_constraintWt + "\n\t" + "Parkfield Seg Err =\t\t"
				+ (float) parkSegRateErr + "\trel. wt = "
				+ relative_aPrioriSegRateWt + "\n\t";

		System.out.println(resultsString);

		// Now with equation weights
		totPredErr = 0;
		slipRateErr = 0;
		eventRateErr = 0;
		aPrioriErr = 0;
		smoothnessErr = 0;
		SlipRateSmoothnessErr = 0;
		grErr = 0;
		parkSegRateErr = 0;
		for (int row = firstRowSegSlipRateData; row <= lastRowSegSlipRateData; row++)
			slipRateErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
					* full_wt[row] * full_wt[row];
		if (relativeSegRateWt > 0)
			for (int row = firstRowSegEventRateData; row <= lastRowSegEventRateData; row++)
				eventRateErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
						* full_wt[row] * full_wt[row];
		if (relative_aPrioriRupWt > 0)
			for (int row = firstRowAprioriData; row <= lastRowAprioriData; row++)
				aPrioriErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
						* full_wt[row] * full_wt[row];
		if (relative_smoothnessWt > 0)
			for (int row = firstRowSmoothnessData; row <= lastRowSmoothnessData; row++)
				smoothnessErr += (d[row] - d_pred[row])
						* (d[row] - d_pred[row]) * full_wt[row] * full_wt[row];
		if (relativeSlipRateSmoothnessWt > 0)
			for (int row = firstRowSlipRateSmoothnessData; row <= lastRowSlipRateSmoothnessData; row++)
				SlipRateSmoothnessErr += (d[row] - d_pred[row])
						* (d[row] - d_pred[row]) * full_wt[row] * full_wt[row];
		if (relativeGR_constraintWt > 0)
			for (int row = firstRowGR_constraintData; row <= lastRowGR_constraintData; row++)
				grErr += (d[row] - d_pred[row]) * (d[row] - d_pred[row])
						* full_wt[row] * full_wt[row];
		if (relative_aPrioriSegRateWt > 0)
			for (int row = firstRowParkSegConstraint; row <= lastRowParkSegConstraint; row++)
				parkSegRateErr += (d[row] - d_pred[row])
						* (d[row] - d_pred[row]) * full_wt[row] * full_wt[row];
		totPredErr = slipRateErr + eventRateErr + aPrioriErr + smoothnessErr + SlipRateSmoothnessErr
				+ grErr + parkSegRateErr;

		System.out.println("\nTotal Pred Err w/ Eq Wts =\t\t"
				+ (float) totPredErr + "\n\t" + "Slip Rate Err =\t\t\t"
				+ (float) slipRateErr + "\trel. wt = 1.0\n\t"
				+ "Event Rate Err =\t\t" + (float) eventRateErr + "\trel. wt = "
				+ relativeSegRateWt + "\n\t" + "A Priori Err =\t\t\t"
				+ (float) aPrioriErr + "\trel. wt = " + relative_aPrioriRupWt
				+ "\n\t" + "Smoothness Err =\t\t" + (float) smoothnessErr
				+ "\trel. wt = " + relative_smoothnessWt + "\n\t"
				+ "Slip Rate Smoothing Err =\t" + (float) SlipRateSmoothnessErr
				+ "\trel. wt = " + relativeSlipRateSmoothnessWt + "\n\t"
				+ "GR Err =\t\t\t" + (float) grErr + "\trel. wt = "
				+ relativeGR_constraintWt + "\n\t" + "Parkfield Seg Err =\t\t"
				+ (float) parkSegRateErr + "\trel. wt = "
				+ relative_aPrioriSegRateWt + "\n\t");

	}

	public void plotStuff(String dirName) {

		// plot orig and final slip rates
		double min = 0, max = num_seg - 1;
		EvenlyDiscretizedFunc origSlipRateFunc = new EvenlyDiscretizedFunc(min,
				max, num_seg);
		EvenlyDiscretizedFunc origUpper95_SlipRateFunc = new EvenlyDiscretizedFunc(
				min, max, num_seg);
		EvenlyDiscretizedFunc origLower95_SlipRateFunc = new EvenlyDiscretizedFunc(
				min, max, num_seg);
		EvenlyDiscretizedFunc finalSlipRateFunc = new EvenlyDiscretizedFunc(
				min, max, num_seg);
		for (int seg = 0; seg < num_seg; seg++) {
			origSlipRateFunc.set(seg, segSlipRate[seg] * (1 - moRateReduction));
			double sigma = subSectionList.get(seg).getSlipRateStdDev() * 1e-3;
			origUpper95_SlipRateFunc.set(seg, (segSlipRate[seg] + 1.96 * sigma)
					* (1 - moRateReduction));
			origLower95_SlipRateFunc.set(seg, (segSlipRate[seg] - 1.96 * sigma)
					* (1 - moRateReduction));
			finalSlipRateFunc.set(seg, finalSegSlipRate[seg]);
		}
		ArrayList sr_funcs = new ArrayList();
		origSlipRateFunc.setName("Orig Slip Rates");
		origUpper95_SlipRateFunc
				.setName("Orig Upper 95% Confidence for Slip Rates");
		origLower95_SlipRateFunc
				.setName("Orig Lower 95% Confidence for Slip Rates");
		finalSlipRateFunc.setName("Final Slip Rates");
		sr_funcs.add(finalSlipRateFunc);
		sr_funcs.add(origSlipRateFunc);
		sr_funcs.add(origUpper95_SlipRateFunc);
		sr_funcs.add(origLower95_SlipRateFunc);
		GraphiWindowAPI_Impl sr_graph = new GraphiWindowAPI_Impl(sr_funcs, "");
		ArrayList<PlotCurveCharacterstics> sr_plotChars = new ArrayList<PlotCurveCharacterstics>();
		sr_plotChars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
				Color.BLACK, 4));
		sr_plotChars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLUE, 2));
		sr_plotChars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLUE, 1));
		sr_plotChars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLUE, 1));
		sr_graph.setPlottingFeatures(sr_plotChars);
		sr_graph.setX_AxisLabel("Subsection");
		sr_graph.setY_AxisLabel("Slip Rate (m/sec)");
		sr_graph.setY_AxisRange(0.0, 0.04);
		sr_graph.setTickLabelFontSize(12);
		sr_graph.setAxisAndTickLabelFontSize(14);
		if (dirName != null) {
			String filename = ROOT_PATH + dirName + "/slipRates";
			try {
				sr_graph.saveAsPDF(filename + ".pdf");
				sr_graph.saveAsPNG(filename + ".png");
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

		// plot orig and final seg event rates
		ArrayList er_funcs = new ArrayList();
		// now fill in final event rates
		EvenlyDiscretizedFunc finalEventRateFunc = new EvenlyDiscretizedFunc(
				min, max, num_seg);
		EvenlyDiscretizedFunc finalPaleoVisibleEventRateFunc = new EvenlyDiscretizedFunc(
				min, max, num_seg);
		for (int seg = 0; seg < num_seg; seg++) {
			finalEventRateFunc.set(seg, finalSegEventRate[seg]);
			finalPaleoVisibleEventRateFunc.set(seg,
					finalPaleoVisibleSegEventRate[seg]);
		}
		finalPaleoVisibleEventRateFunc
				.setName("Final Paleoseismically Visible Event Rates");
		finalEventRateFunc.setName("Final Event Rates (dashed)");
		er_funcs.add(finalPaleoVisibleEventRateFunc);
		er_funcs.add(finalEventRateFunc);
		int num = segRateConstraints.size();
		ArbitrarilyDiscretizedFunc func;
		ArrayList obs_er_funcs = new ArrayList();
		SegRateConstraint constraint;
		for (int c = 0; c < num; c++) {
			func = new ArbitrarilyDiscretizedFunc();
			constraint = segRateConstraints.get(c);
			int seg = constraint.getSegIndex();
			func.set((double) seg - 0.0001, constraint.getLower95Conf());
			func.set((double) seg, constraint.getMean());
			func.set((double) seg + 0.0001, constraint.getUpper95Conf());
			func.setName(constraint.getFaultName());
			obs_er_funcs.add(func);
			er_funcs.add(func);
		}
		// er_funcs.add(obs_er_funcs);
		GraphiWindowAPI_Impl er_graph = new GraphiWindowAPI_Impl(er_funcs, "");
		ArrayList<PlotCurveCharacterstics> plotChars = new ArrayList<PlotCurveCharacterstics>();
		plotChars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE, Color.RED,
				2));
		plotChars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLUE, 1));
		for (int c = 0; c < num; c++)
			plotChars.add(new PlotCurveCharacterstics(
					PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES,
					Color.RED, 1));
		er_graph.setPlottingFeatures(plotChars);
		er_graph.setX_AxisLabel("Subsection");
		er_graph.setY_AxisLabel("Event Rate (per yr)");
		er_graph.setYLog(true);
		er_graph.setTickLabelFontSize(12);
		er_graph.setAxisAndTickLabelFontSize(14);
		if (dirName != null) {
			String filename = ROOT_PATH + dirName + "/eventRates";
			try {
				er_graph.saveAsPDF(filename + ".pdf");
				er_graph.saveAsPNG(filename + ".png");
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

		// plot the final rupture rates
		max = num_rup - 1;
		EvenlyDiscretizedFunc rupRateFunc = new EvenlyDiscretizedFunc(min, max,
				num_rup);
	
		for (int rup = 0; rup < num_rup; rup++) {
			rupRateFunc.set(rup, rupRateSolution[rup]);
		}
		ArrayList rup_funcs = new ArrayList();
		rupRateFunc.setName("Rupture Rates");
		rup_funcs.add(rupRateFunc);
		GraphiWindowAPI_Impl rup_graph = new GraphiWindowAPI_Impl(rup_funcs,
				"Rupture Rates");

		// PLOT MFDs
		ArrayList mfd_funcs = new ArrayList();
		mfd_funcs.add(magFreqDist);
		EvenlyDiscretizedFunc cumMagFreqDist = magFreqDist
				.getCumRateDistWithOffset();
		cumMagFreqDist.setInfo("Cumulative Mag Freq Dist");
		mfd_funcs.add(cumMagFreqDist);
		// add average seg participation MFD
		mfd_funcs.add(aveOfSegPartMFDs);
		EvenlyDiscretizedFunc cumAveOfSegPartMFDs = aveOfSegPartMFDs
				.getCumRateDistWithOffset();
		cumAveOfSegPartMFDs.setInfo("cumulative " + aveOfSegPartMFDs.getInfo());
		// mfd_funcs.add(cumAveOfSegPartMFDs);
		// the following is just a check
		// System.out.println("orig/smoothed MFD moRate ="+
		// (float)(magFreqDist.getTotalMomentRate()/smoothedMagFreqDist.getTotalMomentRate()));
		// add a GR dist matched at M=6.5 and with a bValue=1
		GutenbergRichterMagFreqDist gr = getGR_Dist_fit();
		if (gr != null) {
			mfd_funcs.add(gr);
			EvenlyDiscretizedFunc cumGR = gr.getCumRateDistWithOffset();
			cumGR
					.setName("Cum GR Dist fit at cum M=6.5, matched moment rate, and /w b=1");
			mfd_funcs.add(cumGR);
		} else
			System.out
					.println("WARNING - couldn't generate fitted GR dist (Mmax greater than 9?)\n");

		/*
		 * if(relativeGR_constraintWt > 0.0) { double deltaMag = 0.1;
		 * ArbitrarilyDiscretizedFunc grConstraintFunc = new
		 * ArbitrarilyDiscretizedFunc(); int numGR_constraints =
		 * lastRowGR_constraintData-firstRowGR_constraintData+1; for(int i=0; i <
		 * numGR_constraints; i++) { int row = i+firstRowGR_constraintData;
		 * double mag = smallestGR_constriantMag + i*deltaMag;
		 * grConstraintFunc.set(mag, d[row]); } grConstraintFunc.setName("GR
		 * constraint values"); mfd_funcs.add(grConstraintFunc); }
		 */

		GraphiWindowAPI_Impl mfd_graph = new GraphiWindowAPI_Impl(mfd_funcs,
				"Magnitude Frequency Distributions");
		mfd_graph.setYLog(true);
		mfd_graph.setY_AxisRange(1e-5, 0.2);
		mfd_graph.setX_AxisRange(5.6, 8.7);
		mfd_graph.setX_AxisLabel("Magnitude");
		mfd_graph.setY_AxisLabel("Rate (per yr)");

		ArrayList<PlotCurveCharacterstics> plotMFD_Chars = new ArrayList<PlotCurveCharacterstics>();
		plotMFD_Chars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLUE, 3));
		plotMFD_Chars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE, Color.RED,
				3));
		plotMFD_Chars.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.GREEN, 3));
		if (gr != null) {
			plotMFD_Chars.add(new PlotCurveCharacterstics(
					PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
					Color.BLUE, 1));
			plotMFD_Chars.add(new PlotCurveCharacterstics(
					PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
					Color.RED, 1));
		}
		mfd_graph.setPlottingFeatures(plotMFD_Chars);
		mfd_graph.setTickLabelFontSize(12);
		mfd_graph.setAxisAndTickLabelFontSize(14);
		if (dirName != null) {
			String filename = ROOT_PATH + dirName + "/MFDs";
			try {
				mfd_graph.saveAsPDF(filename + ".pdf");
				mfd_graph.saveAsPNG(filename + ".png");
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

		// PLOT RATE AT WHICH SECTIONS ENDS REPRESENT RUPTURE ENDS
		min = 0;
		max = num_seg;
		EvenlyDiscretizedFunc rateOfRupEndsOnSegFunc = new EvenlyDiscretizedFunc(
				min, max, num_seg + 1);
		for (int seg = 0; seg < num_seg + 1; seg++) {
			rateOfRupEndsOnSegFunc.set(seg, rateOfRupEndsOnSeg[seg]);
		}
		ArrayList seg_funcs = new ArrayList();
		rateOfRupEndsOnSegFunc
				.setName("Rate that section ends represent rupture ends");
		seg_funcs.add(finalSlipRateFunc);
		seg_funcs.add(finalPaleoVisibleEventRateFunc);
		// add paleoseismic obs
		for (int i = 0; i < obs_er_funcs.size(); i++)
			seg_funcs.add(obs_er_funcs.get(i));
		seg_funcs.add(rateOfRupEndsOnSegFunc);

		GraphiWindowAPI_Impl seg_graph = new GraphiWindowAPI_Impl(seg_funcs, "");
		ArrayList<PlotCurveCharacterstics> plotChars2 = new ArrayList<PlotCurveCharacterstics>();
		plotChars2.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLUE, 2));
		plotChars2.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE, Color.RED,
				2));
		for (int c = 0; c < num; c++)
			plotChars2.add(new PlotCurveCharacterstics(
					PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES,
					Color.RED, 1));
		plotChars2.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
				Color.BLACK, 2));
		seg_graph.setPlottingFeatures(plotChars2);
		seg_graph.setX_AxisLabel("Subsection");
		seg_graph.setY_AxisLabel("Rates");
		seg_graph.setYLog(true);
		seg_graph.setTickLabelFontSize(12);
		seg_graph.setAxisAndTickLabelFontSize(14);
		if (dirName != null) {
			String filename = ROOT_PATH + dirName + "/endpointRates";
			try {
				seg_graph.saveAsPDF(filename + ".pdf");
				seg_graph.saveAsPNG(filename + ".png");
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}

	}

	public void plotHistograms() {

		ArrayList funcs = new ArrayList();
		funcs.add(meanMagHistorgram);
		funcs.add(magHistorgram);
		GraphiWindowAPI_Impl mHist_graph = new GraphiWindowAPI_Impl(funcs,
				"Mag Histograms");
		// mfd_graph.setYLog(true);
		// mfd_graph.setY_AxisRange(1e-5, 1);
		mHist_graph.setX_AxisRange(3.5, 9.0);

		// make a numSegInRupHistogram
		SummedMagFreqDist numSegInRupHistogram = new SummedMagFreqDist(1.0,
				num_seg, 1.0);
		for (int r = 0; r < numSegInRup.length; r++)
			numSegInRupHistogram.add((double) numSegInRup[r], 1.0);
		numSegInRupHistogram.setName("Num Segments In Rupture Histogram");
		ArrayList funcs2 = new ArrayList();
		funcs2.add(numSegInRupHistogram);
		GraphiWindowAPI_Impl graph = new GraphiWindowAPI_Impl(funcs2,
				"Num Segments In Rupture Histogram");

	}

	public GutenbergRichterMagFreqDist getGR_Dist_fit() {
		double magMin = (double) Math.round(10 * rupMeanMag[this
				.getParkfieldRuptureIndex()]) / 10;
		double cumRate = magFreqDist.getCumRate(6.5)
				* Math.pow(10, 6.5 - magMin); // assumes b-value of 1
		int num = (int) Math.round((9.0 - magMin) / 0.1 + 1);
		GutenbergRichterMagFreqDist gr = new GutenbergRichterMagFreqDist(
				magMin, num, 0.1);
		double moRate = totMoRate * (1 - moRateReduction);
		try {
			gr.setAllButMagUpper(magMin, moRate, cumRate, 1.0, true);
			gr
					.setName("GR Dist fit at cum M=6.5, matched moment rate, and /w b=1");
			return gr;
		} catch (Exception e) {
			return null;
		}
	}

	/**
	 * This returns the probability that the given magnitude event will be
	 * observed at the ground surface. This is based on equation 4 of Youngs et
	 * al. [2003, A Methodology for Probabilistic Fault Displacement Hazard
	 * Analysis (PFDHA), Earthquake Spectra 19, 191-219] using the coefficients
	 * they list in their appendix for "Data from Wells and Coppersmith (1993)
	 * 276 worldwide earthquakes". Their function has the following
	 * probabilities:
	 * 
	 * mag prob 5 0.10 6 0.45 7 0.87 8 0.98 9 1.00
	 * 
	 * @return
	 */
	private double getProbVisible(double mag) {
		return Math.exp(-12.51 + mag * 2.053)
				/ (1.0 + Math.exp(-12.51 + mag * 2.053));
		/*
		 * Ray & Glenn's equation if(mag <= 5) return 0.0; else if (mag <= 7.6)
		 * return -0.0608*mag*mag + 1.1366*mag + -4.1314; else return 1.0;
		 */
	}

	/**
	 * It gets all the subsections for SoSAF and prints them on console
	 * 
	 * @param args
	 */
	public static void main(String[] args) {
		
		SoSAF_SubSectionInversion_v3 soSAF_SubSections = new SoSAF_SubSectionInversion_v3();

		/* */
		long runTime = System.currentTimeMillis();
		// System.out.println("Starting Inversion");

		int maxSubsectionLength = 7;
		int numSegForSmallestRups = 2;
		String deformationModel = "D2.1";
		String slipModelType = TAPERED_SLIP_MODEL;
		MagAreaRelationship magAreaRel = new HanksBakun2002_MagAreaRel();
		// MagAreaRelationship magAreaRel = new Ellsworth_B_WG02_MagAreaRel();
		double relativeSegRateWt = 1;
		double relative_aPrioriRupWt = 1;
		double relative_smoothnessWt = 0; // 10 (Ned) or 10000(MP)
		double relativeSlipRateSmoothnessWt = 1000; // 1000
		boolean wtedInversion = true;
		double minRupRate = 0;
		boolean applyProbVisible = true;
		double moRateReduction = 0.1;
		boolean transitionAseisAtEnds = true;
		boolean transitionSlipRateAtEnds = true;
		boolean slipRateConstraintAtSegCentersOnly = false;
		int slipRateSmoothing = 1; // Only used if slipRateConstraintAtSegCentersOnly=false
		double relativeGR_constraintWt = 0; // 1e6 (Ned) // 1e4 (Morgan)
		// double grConstraintBvalue = 0;
		// double grConstraintRateScaleFactor = 0.83; // for case where b=0
		double grConstraintBvalue = 1;
		double grConstraintRateScaleFactor = 0.89; // for case where b=1
		double relative_aPrioriSegRateWt = 0;

		soSAF_SubSections.doInversion(maxSubsectionLength,
				numSegForSmallestRups, deformationModel, slipModelType,
				magAreaRel, relativeSegRateWt, relative_aPrioriRupWt,
				relative_smoothnessWt, relativeSlipRateSmoothnessWt, wtedInversion, minRupRate,
				applyProbVisible, moRateReduction, transitionAseisAtEnds,
				transitionSlipRateAtEnds, slipRateConstraintAtSegCentersOnly, slipRateSmoothing,
				relativeGR_constraintWt, grConstraintBvalue,
				grConstraintRateScaleFactor, relative_aPrioriSegRateWt);

		runTime = (System.currentTimeMillis() - runTime) / 1000;
		System.out
				.println("Done with Inversion after " + runTime + " seconds.");

		soSAF_SubSections.writeFinalStuff();
		soSAF_SubSections.writePredErrorInfo();
		// soSAF_SubSections.plotHistograms();

		String dirName = "test";
		File file = new File(soSAF_SubSections.ROOT_PATH + dirName);
		file.mkdirs();
		soSAF_SubSections.plotStuff(null);
		soSAF_SubSections.plotOrWriteSegPartMFDs(dirName, true);
		soSAF_SubSections.writeAndPlotNonZeroRateRups(dirName, true);

		/*
		 * // this searches for the best GR constraint scale factor //
		 * for(double scale = 0.87; scale <0.939; scale +=0.01) { // last test
		 * for CASE 8 (used in paper) for(double scale = 0.75; scale <0.9; scale
		 * +=0.01) { // last test for CASE 9 (b=0)
		 * System.out.println("\n********* RUN FOR SCALE "+(float)scale+"
		 * **********\n");
		 * soSAF_SubSections.doInversion(maxSubsectionLength,numSegForSmallestRups,deformationModel,
		 * slipModelType, magAreaRel, relativeSegRateWt, relative_aPrioriRupWt,
		 * relative_smoothnessWt, relativeSlipRateSmoothnessWt, wtedInversion, minRupRate, applyProbVisible,
		 * moRateReduction, transitionAseisAtEnds, transitionSlipRateAtEnds,
		 * slipRateConstraintAtSegCentersOnly, slipRateSmoothing, relativeGR_constraintWt, grConstraintBvalue,
		 * scale, relative_aPrioriSegRateWt);
		 * //soSAF_SubSections.writeFinalStuff();
		 * soSAF_SubSections.writePredErrorInfo(); }
		 */

		/*
		 * ArrayList<FaultSectionPrefData> subsectionList =
		 * soSAF_SubSections.getAllSubsections(); for(int i=0; i<subsectionList.size();
		 * ++i) { FaultSectionPrefData subSection = subsectionList.get(i);
		 * System.out.println(i+"\t"+subSection.getSectionName()+"\t"+(float)subSection.getLength()); //
		 * System.out.println(subSection.getFaultTrace()); }
		 */
		/*
		 * // write rup names to a file System.out.println("Writing file for
		 * short rupture names");
		 * soSAF_SubSections.writeRupNames("ShortRupNames.txt");
		 *  // computer and print seg Rate constraints
		 * System.out.println("Writing Seg Rate constraints");
		 * soSAF_SubSections.computeSegRateConstraints(); for(int i=0; i<soSAF_SubSections.segRateConstraints.size();
		 * ++i) { SegRateConstraint segRateConstraint =
		 * soSAF_SubSections.segRateConstraints.get(i);
		 * System.out.println(segRateConstraint.getFaultName()+","+segRateConstraint.getMean()); }
		 */

	}

}
