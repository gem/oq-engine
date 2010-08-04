package scratch.kevin;

import java.io.FileWriter;
import java.io.IOException;

import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.XMLWriter;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.gridComputing.GridResources;
import org.opensha.commons.gridComputing.ResourceProvider;
import org.opensha.commons.gridComputing.StorageHost;
import org.opensha.commons.gridComputing.SubmitHost;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.calc.hazardMap.old.HazardMapCalculationParameters;
import org.opensha.sha.calc.hazardMap.old.HazardMapJob;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

public class MetadataSaver implements ParameterChangeWarningListener {

	public MetadataSaver() {
		Document document = DocumentHelper.createDocument();
		Element root = document.addElement( "OpenSHA" );


//		EqkRupForecast erf = new MeanUCERF2();
		EqkRupForecast erf = new Frankel02_AdjustableEqkRupForecast();
//		erf.getAdjustableParameterList().getParameter(UCERF2.BACK_SEIS_NAME).setValue(UCERF2.BACK_SEIS_INCLUDE);
//		TimeSpan span = new TimeSpan(TimeSpan.YEARS, TimeSpan.YEARS);
//		span.setDuration(30);
//		span.setStartTime(2017);
//		erf.setTimeSpan(span);

		AttenuationRelationship imr = new CB_2008_AttenRel(this);
		// set default parameters
		imr.setParamDefaults();
		// set the Intensity Measure Type
//		imr.setIntensityMeasure(PGA_Param.NAME);
		imr.setIntensityMeasure(SA_Param.NAME);
		imr.getParameter(PeriodParam.NAME).setValue(new
                Double(0.5));
		
		//Region region = new RELM_TestingRegion();
		//GriddedRegion gridded = new GriddedRegion(region.getRegionOutline(), BorderType.MERCATOR_LINEAR, 0.1);
		GriddedRegion gridded = 
			new CaliforniaRegions.RELM_TESTING_GRIDDED();
//		Region gridded = null;
//		try {
//			gridded = new EvenlyGriddedRectangularGeographicRegion(33.5, 34.8, -120.0, -116.0, 0.02);
//		} catch (RegionConstraintException e1) {
//			// TODO Auto-generated catch block
//			e1.printStackTrace();
//		}
		
		String jobName = "Schema Test";
		String jobID = System.currentTimeMillis() + "";
		int sitesPerJob = 100;
		double maxSourceDistance = 200;
		boolean useCVM = false;
		boolean serializeERF = true;
		String configFileName = jobID + ".xml";
		int maxWallTime = 40;
		ResourceProvider rp = ResourceProvider.HPC();
		SubmitHost submit = SubmitHost.AFTERSHOCK;
		StorageHost storage = StorageHost.HPC;
		String email = "kmilner@usc.edu";
		
		GridResources resources = new GridResources(submit, rp, storage);
		HazardMapCalculationParameters calcParams = new HazardMapCalculationParameters(maxWallTime, sitesPerJob, maxSourceDistance, useCVM, serializeERF);
		
		HazardMapJob job = new HazardMapJob(resources, calcParams, jobID, jobName, email, configFileName);
//		HazardMapJob job = new HazardMapJob(jobName, rp_host, rp_batchScheduler, rp_javaPath, rp_storagePath, rp_globusrsl, repo_host, repo_storagePath, HazardMapJob.DEFAULT_SUBMIT_HOST, HazardMapJob.DEFAULT_SUBMIT_HOST_PATH, HazardMapJob.DEFAULT_DEPENDENCY_PATH, sitesPerJob, useCVM, saveERF, metadataFileName);

		root = erf.toXMLMetadata(root);
		root = imr.toXMLMetadata(root);
		root = gridded.toXMLMetadata(root);
		root = job.toXMLMetadata(root);
		

		XMLWriter writer;


		try {
			OutputFormat format = OutputFormat.createPrettyPrint();
			writer = new XMLWriter(System.out, format);
			writer.write(document);
			writer.close();

			writer = new XMLWriter(new FileWriter("output.xml"), format);
			writer.write(document);
			writer.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}


	}
	
	public Element writeCalculationParams(Element root) {
		Element xml = root.addElement("calculationParameters");
		xml.addAttribute("maxSourceDistance", "200");
		
		return root;
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		new MetadataSaver();
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {
		// TODO Auto-generated method stub

	}

}
