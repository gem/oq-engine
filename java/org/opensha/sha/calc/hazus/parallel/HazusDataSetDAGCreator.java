package org.opensha.sha.calc.hazus.parallel;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.gridComputing.condor.DAG;
import org.opensha.commons.gridComputing.condor.SubmitScriptForDAG;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.calc.hazardMap.components.CalculationInputsXMLFile;
import org.opensha.sha.calc.hazardMap.components.CalculationSettings;
import org.opensha.sha.calc.hazardMap.components.CurveResultsArchiver;
import org.opensha.sha.calc.hazardMap.dagGen.HazardDataSetDAGCreator;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class generates a simple Condor DAG for a given ERF, IMR Hash Map(s),
 * and list of sites.
 * 
 * This DAG is meant to be run on a shared filesystem, where the output directory
 * for DAG generation is also visible on the compute nodes/slots. It could be extended
 * in the future to use Globus and GridFTP to get around this limitation.
 * 
 * @author kevin
 *
 */
public class HazusDataSetDAGCreator extends HazardDataSetDAGCreator {
	
	private int durationYears;
	private GriddedRegion region;

	/**
	 * Convenience constructor for if you already have the inputs from an XML file.
	 * 
	 * @param inputs
	 * @param javaExec
	 * @param jarFile
	 * @throws InvocationTargetException 
	 */
	public HazusDataSetDAGCreator(CalculationInputsXMLFile inputs, String javaExec, String jarFile,
			int durationYears, GriddedRegion region) throws InvocationTargetException {
		this(inputs.getERF(), inputs.getIMRMaps(), inputs.getSites(), inputs.getCalcSettings(),
				inputs.getArchiver(), javaExec, jarFile, durationYears, region);
	}

	/**
	 * Main constructor with objects/info necessary for hazus data set calculation.
	 * 
	 * @param erf - The ERF
	 * @param imrMaps - A list of IMR/TectonicRegion hash maps
	 * @param sites - The list of sites that need to be calculated. All site parameters should already be set
	 * @param calcSettings - Some simple calculation settings (such as X values, cutoff distance)
	 * @param archiver - The archiver used to store curves once calculated
	 * @param javaExec - The path to the java executable
	 * @param jarFile - The path to the jar file used for calculation.
	 * @throws InvocationTargetException 
	 */
	public HazusDataSetDAGCreator(EqkRupForecastAPI erf,
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
			List<Site> sites,
			CalculationSettings calcSettings,
			CurveResultsArchiver archiver,
			String javaExec,
			String jarFile,
			int durationYears,
			GriddedRegion region) throws InvocationTargetException {
		super(erf, getHAZUSMaps(imrMaps), getIMTList(imrMaps), sites, calcSettings, archiver, javaExec, jarFile);
		this.durationYears = durationYears;
		this.region = region;
	}
	
	/**
	 * Main constructor with objects/info necessary for hazus data set calculation.
	 * 
	 * @param erf - The ERF
	 * @param imrMaps - A list of IMR/TectonicRegion hash maps
	 * @param sites - The list of sites that need to be calculated. All site parameters should already be set
	 * @param calcSettings - Some simple calculation settings (such as X values, cutoff distance)
	 * @param archiver - The archiver used to store curves once calculated
	 * @param javaExec - The path to the java executable
	 * @param jarFile - The path to the jar file used for calculation.
	 * @throws InvocationTargetException 
	 */
	public HazusDataSetDAGCreator(EqkRupForecastAPI erf,
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
			List<DependentParameterAPI<Double>> imts,
			List<Site> sites,
			CalculationSettings calcSettings,
			CurveResultsArchiver archiver,
			String javaExec,
			String jarFile,
			int durationYears,
			GriddedRegion region) throws InvocationTargetException {
		super(erf, getHAZUSMaps(imrMaps), validateIMTList(imts), sites, calcSettings, archiver, javaExec, jarFile);
		this.durationYears = durationYears;
		this.region = region;
	}
	
	private static List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> getHAZUSMaps(
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps) throws InvocationTargetException {
		if (imrMaps.size() == 1) {
			ArrayList<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> newIMRMaps =
				new ArrayList<HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();
			
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> origMap = imrMaps.get(0);
			
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> pgaMap =
				new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> pgvMap =
				new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> sa03Map =
				new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> sa10Map =
				new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();
			
			for (TectonicRegionType trt : origMap.keySet()) {
				ScalarIntensityMeasureRelationshipAPI imr = origMap.get(trt);
				
				pgaMap.put(trt, imr);
				pgvMap.put(trt, imr);
				sa03Map.put(trt, imr);
				sa10Map.put(trt, imr);
			}
			newIMRMaps.add(pgaMap);
			newIMRMaps.add(pgvMap);
			newIMRMaps.add(sa03Map);
			newIMRMaps.add(sa10Map);
			return newIMRMaps;
		} else if (imrMaps.size() == 4) {
			// this might already be set up for HAZUS, but lets just make sure
			validateHAZUSMap(imrMaps);
			return imrMaps;
		} else {
			throw new IllegalArgumentException("imrMaps must either be of size 1, or size 4 and already" +
					"setup for HAZUS.");
		}
	}
	
	protected static void validateHAZUSMap(
				List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps) {
		if (imrMaps.size() != 4)
			throw new RuntimeException("imrMaps must contain exactly 4 elements");
	}
	
	public static List<DependentParameterAPI<Double>> validateIMTList(List<DependentParameterAPI<Double>> imts) {
		if (imts.size() != 4)
			throw new IllegalArgumentException("IMT list must be of size 4");
		
		for (int i=0; i<4; i++) {
			DoubleParameter periodParam = null;
			DependentParameterAPI<Double> imt = imts.get(i);
			switch (i) {
			
			case 0:
				if (imt.getName() != PGA_Param.NAME)
					throw new RuntimeException("HAZUS IMT 1 must be of type PGA");
				break;
			case 1:
				if (imt.getName() != PGV_Param.NAME)
					throw new RuntimeException("HAZUS IMT 2 must be of type PGA");
				break;
			case 2:
				if (imt.getName() != SA_Param.NAME)
					throw new RuntimeException("HAZUS IMT 3 must be of type PGA");
				periodParam = (DoubleParameter) imt.getIndependentParameter(PeriodParam.NAME);
				if (periodParam.getValue() != 0.3)
					throw new RuntimeException("HAZUS IMT 1 must have SA period of 0.3");
				break;
			case 3:
				if (imt.getName() != SA_Param.NAME)
					throw new RuntimeException("HAZUS IMT 4 must be of type PGA");
				periodParam = (DoubleParameter) imt.getIndependentParameter(PeriodParam.NAME);
				if (periodParam.getValue() != 1.0)
					throw new RuntimeException("HAZUS IMT 1 must have SA period of 0.3");
				break;
			}
		}
		return imts;
	}
	
	public static ArrayList<DependentParameterAPI<Double>> getIMTList(
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps) {
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> map0 = imrMaps.get(0);
		ScalarIntensityMeasureRelationshipAPI testIMR = map0.get(map0.keySet().iterator().next());
		
		ArrayList<DependentParameterAPI<Double>> imts = new ArrayList<DependentParameterAPI<Double>>();
		
		testIMR.setIntensityMeasure(PGA_Param.NAME);
		imts.add((DependentParameterAPI<Double>) testIMR.getIntensityMeasure().clone());
		
		testIMR.setIntensityMeasure(PGV_Param.NAME);
		imts.add((DependentParameterAPI<Double>) testIMR.getIntensityMeasure().clone());
		
		DependentParameterAPI<Double> saParam;
		ParameterAPI<Double> periodParam;
		
		testIMR.setIntensityMeasure(SA_Param.NAME);
		saParam = (DependentParameterAPI<Double>) testIMR.getIntensityMeasure().clone();
		periodParam = (ParameterAPI<Double>) saParam.getIndependentParameter(PeriodParam.NAME);
		periodParam.setValue(0.3);
		imts.add(saParam);
		
		testIMR.setIntensityMeasure(SA_Param.NAME);
		saParam = (DependentParameterAPI<Double>) testIMR.getIntensityMeasure().clone();
		periodParam = (ParameterAPI<Double>) saParam.getIndependentParameter(PeriodParam.NAME);
		periodParam.setValue(1.0);
		imts.add(saParam);
		
		return imts;
	}
	
	private String getIMRMetadata() {
		String meta = null;
		
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap1 = this.imrMaps.get(0);
		if (imrMap1.size() == 1) {
			ScalarIntensityMeasureRelationshipAPI imr = imrMap1.values().iterator().next();
			meta = "IMR = " + imr.getName() + "; " + imr.getOtherParamsList().getParameterListMetadataString();
		} else {
			meta = "IMR = (multiple)";
			for (TectonicRegionType trt : imrMap1.keySet()) {
				ScalarIntensityMeasureRelationshipAPI imr = imrMap1.get(trt);
				meta += "; " + trt.toString() + " = " + imr.getName() + "; " + imr.getAllParamMetadata();
			}
		}
		
		return meta;
	}
	
	private String getSitesMetadata() {
		double minLat = region.getMinGridLat();
		double maxLat = region.getMaxGridLat();
		double minLon = region.getMinGridLon();
		double maxLon = region.getMaxGridLon();
		double spacing = region.getSpacing();
		
		return "Min Longitude = "+minLon+"; Max Longitude = "+maxLon+"; " +
				"Min  Latitude = "+minLat+"; Max  Latitude = "+maxLat+"; Grid Spacing = "+spacing;
	}
	
	private String getERFMetadata() {
		return "Eqk Rup Forecast = " + erf.getName() + "; "
			+ erf.getAdjustableParameterList().getParameterListMetadataString();
	}
	
	private String writeMetadataFile(String odir) throws IOException {
		String fileName = odir + "metadata.dat";
		FileWriter fw = new FileWriter(fileName);
		
		// line 1, IMR
		fw.write(getIMRMetadata() + "\n");
		// line 2, blank
		fw.write("" + "\n");
		// line 3, Sites
		fw.write(getSitesMetadata() + "\n");
		// line 4, blank
		fw.write("" + "\n");
		// line 5, ERF
		fw.write(getERFMetadata() + "\n");
		// line 6, duration
		fw.write("Duration = " + erf.getTimeSpan().getDuration(TimeSpan.YEARS) + "\n");
		// line 7, RP
		fw.write("Return Period = " + HazusDataSetAssmbler.METADATA_RP_REPLACE_STR + "\n");
		// line 8, cutoff
		fw.write("Maximum Site Source Distance = " + this.calcSettings.getMaxSourceDistance() + "\n");
		
		fw.close();
		return fileName;
	}

	@Override
	protected DAG getPostDAG(File outputDir) throws IOException {
		DAG postDAG = new DAG();
		
		String odir = outputDir.getAbsolutePath();
		if (!odir.endsWith(File.separator))
			odir += File.separator;
		
		String metadataFile = writeMetadataFile(odir);
		
		String executable = javaExec;
		String vmArgs = "-classpath " + jarFile + " " + HazusDataSetAssmbler.class.getName();
		String progArgs = archiver.getStoreDir().getPath() + " " + durationYears + " " + metadataFile;
		String arguments = vmArgs + " " + progArgs;
		SubmitScriptForDAG assembleJob = new SubmitScriptForDAG("assemble", executable, arguments,
				"/tmp", universe, true);
		assembleJob.setRequirements(getRequirements());
		assembleJob.writeScriptInDir(odir);
		assembleJob.setComment("Assemble curves into HAZUS dataset");
		
		postDAG.addJob(assembleJob);
		
		return postDAG;
	}
}
