package org.opensha.sha.calc.hazardMap.dagGen;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.text.DecimalFormat;
import java.util.HashMap;
import java.util.List;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.opensha.commons.data.Site;
import org.opensha.commons.gridComputing.condor.DAG;
import org.opensha.commons.gridComputing.condor.SubmitScriptForDAG;
import org.opensha.commons.gridComputing.condor.DAG.DAG_ADD_LOCATION;
import org.opensha.commons.gridComputing.condor.SubmitScript.Universe;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.HazardCurveDriver;
import org.opensha.sha.calc.hazardMap.components.CalculationInputsXMLFile;
import org.opensha.sha.calc.hazardMap.components.CalculationSettings;
import org.opensha.sha.calc.hazardMap.components.CurveResultsArchiver;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
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
public class HazardDataSetDAGCreator {

	public static final String ERF_SERIALIZED_FILE_NAME = "erf.obj";

	protected EqkRupForecastAPI erf;
	protected List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps;
	private List<DependentParameterAPI<Double>> imts;

	protected List<Site> sites;
	protected CalculationSettings calcSettings;
	protected CurveResultsArchiver archiver;
	protected String javaExec;
	protected String jarFile;
	
	private int heapSize = 2048;
	
	private String requirements = null;

	private DecimalFormat curveIndexFormat;

	protected Universe universe = Universe.VANILLA;
	
	public static int DAGMAN_MAX_IDLE = 50;
	public static int DAGMAN_MAX_PRE = 3;
	public static int DAGMAN_MAX_POST = 5;

	/**
	 * Convenience constructor for if you already have the inputs from an XML file.
	 * 
	 * @param inputs
	 * @param javaExec
	 * @param jarFile
	 */
	public HazardDataSetDAGCreator(CalculationInputsXMLFile inputs, String javaExec, String jarFile) {
		this(inputs.getERF(), inputs.getIMRMaps(), inputs.getIMTs(), inputs.getSites(), inputs.getCalcSettings(),
				inputs.getArchiver(), javaExec, jarFile);
	}

	/**
	 * Main constructor with objects/info necessary for hazard data set calculation.
	 * 
	 * @param erf - The ERF
	 * @param imrMaps - A list of IMR/TectonicRegion hash maps
	 * @param imts - A list of imt's for each imrMap (or null to use IMT from IMR)
	 * @param sites - The list of sites that need to be calculated. All site parameters should already be set
	 * @param calcSettings - Some simple calculation settings (such as X values, cutoff distance)
	 * @param archiver - The archiver used to store curves once calculated
	 * @param javaExec - The path to the java executable
	 * @param jarFile - The path to the jar file used for calculation.
	 */
	public HazardDataSetDAGCreator(EqkRupForecastAPI erf,
			List<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>> imrMaps,
			List<DependentParameterAPI<Double>> imts,
			List<Site> sites,
			CalculationSettings calcSettings,
			CurveResultsArchiver archiver,
			String javaExec,
			String jarFile) {
		this.erf = erf;
		this.imrMaps = imrMaps;
		this.imts = imts;
		this.sites = sites;
		this.calcSettings = calcSettings;
		this.archiver = archiver;
		String fstr = "";
		for (int i=0; i<(sites.size() + "").length(); i++)
			fstr += "0";
		curveIndexFormat = new DecimalFormat(fstr);
		this.javaExec = javaExec;
		this.jarFile = jarFile;
	}
	
	private void writeCalcWrapperScript(String scriptFile, int startIndex, String xmlFile) throws IOException {
		String newJarFile = "openSHA_" + startIndex + ".jar";
		String javaCommand = javaExec +  " -Xmx" + heapSize + "M" + " -classpath $jarDir/" + newJarFile + " "
					+ HazardCurveDriver.class.getName() + " " + xmlFile;
		
		FileWriter fw = new FileWriter(scriptFile);
		
		fw.write("#!/bin/bash" + "\n");
		fw.write("" + "\n");
		fw.write("set -o errexit" + "\n");
		fw.write("" + "\n");
//		fw.write("# try /scratch, default to /tmp if not" + "\n");
//		fw.write("jarDir=\"/scratch\"" + "\n");
//		fw.write("if [[ ! -e $jarDir ]];then" + "\n");
		fw.write("jarDir=\"/tmp\"" + "\n");
//		fw.write("fi" + "\n");
		fw.write("" + "\n");
		fw.write("cp " + jarFile + " $jarDir/" + newJarFile + "\n");
		fw.write("" + "\n");
		fw.write(javaCommand + "\n");
		fw.write("exit $?" + "\n");
		
		fw.close();
	}
	
	/**
	 * Can be overridden to add jobs at the start of the workflow
	 * 
	 * @return
	 * @throws IOException 
	 */
	protected DAG getPreDAG(File outputDir) throws IOException {
		return null;
	}
	
	/**
	 * Can be overridden to add jobs at the end of the workflow
	 * 
	 * @return
	 * @throws IOException 
	 */
	protected DAG getPostDAG(File outputDir) throws IOException {
		return null;
	}

	/**
	 * Writes the DAG to the specified output directory. It will the task into many small tasks
	 * as specified by sitesPerJob. It can also be automatically submitted if the run is true.
	 * 
	 * @param outputDir
	 * @param sitesPerJob
	 * @param run
	 * @throws IOException
	 */
	public void writeDAG(File outputDir, int sitesPerJob, boolean run) throws IOException {
		if (sitesPerJob < 1)
			throw new IllegalArgumentException("curvesPerJob must be >= 1");
		// create the output dir
		if (!outputDir.exists()) {
			if (!outputDir.mkdir())
				throw new IOException("Output directory '" + outputDir.getPath() + "' does not exist" +
				" and could not be created.");
		}
		String odir = outputDir.getAbsolutePath();
		if (!odir.endsWith(File.separator))
			odir += File.separator;

		String serializedERFFile = null;
		if (calcSettings.isSerializeERF())
			serializedERFFile = serializeERF(odir);

		int numSites = sites.size();

		DAG dag = new DAG();

		new File(odir + "log").mkdir();
		new File(odir + "out").mkdir();
		new File(odir + "err").mkdir();

		for (int startIndex=0; startIndex<numSites; startIndex+=sitesPerJob) {
			int endIndex = startIndex + sitesPerJob - 1;
			if (endIndex > numSites - 1)
				endIndex = numSites - 1;
			
			System.out.println("Writing job for curves " + startIndex + " => " + endIndex);

			String jobName = "Curves_" + curveIndexFormat.format(startIndex) + "_" + curveIndexFormat.format(endIndex);
			String xmlFile = writeCurveJobXML(odir, startIndex, endIndex, jobName, serializedERFFile);
			String scriptFile = odir + jobName + ".sh";
			writeCalcWrapperScript(scriptFile, startIndex, xmlFile);
			String executable = "/bin/bash";
			String arguments = scriptFile;
			SubmitScriptForDAG job = new SubmitScriptForDAG(jobName, executable, arguments,
					"/tmp", universe, true);
			job.setRequirements(requirements);
			
			job.writeScriptInDir(odir);
			job.setComment("Calculates curves " + startIndex + "->" + endIndex + ", inclusive");

			dag.addJob(job);
		}
		DAG preDAG = getPreDAG(outputDir);
		DAG postDAG = getPostDAG(outputDir);
		if (preDAG != null)
			dag.addDAG(preDAG, DAG_ADD_LOCATION.BEFORE_ALL);
		if (postDAG != null)
			dag.addDAG(postDAG, DAG_ADD_LOCATION.AFTER_ALL);

		String dagFileName = odir + "main.dag";

		System.out.println("Writing DAG: " + dagFileName + " (" + dag.getNumJobs() + " jobs)");
		dag.writeDag(dagFileName);
		
		System.out.println("Writing DAG submit script");
		createSubmitDAGScript(odir, run);
	}

	private String writeCurveJobXML(String odir, int startIndex, int endIndex, String jobName,
			String serializedERFFile) throws IOException {
		String fileName = odir + jobName + "_input.xml";

		// get subset of sites for job
		List<Site> newSites = sites.subList(startIndex, endIndex+1);

		// create inputs XML file
		CalculationInputsXMLFile xml = new CalculationInputsXMLFile(erf, imrMaps, imts, newSites, calcSettings, archiver);

		xml.setSerialized(serializedERFFile);

		// write to XML
		Document doc = XMLUtils.createDocumentWithRoot();
		xml.toXMLMetadata(doc.getRootElement());

		XMLUtils.writeDocumentToFile(fileName, doc);

		return fileName;
	}

	private String serializeERF(String odir) throws IOException {
		erf.updateForecast();
		String serializedERFFile = odir + ERF_SERIALIZED_FILE_NAME;
		FileUtils.saveObjectInFile(serializedERFFile, erf);
		return serializedERFFile;
	}

	public Universe getUniverse() {
		return universe;
	}

	public void setUniverse(Universe universe) {
		this.universe = universe;
	}

	/**
	 * Create a DAG submit script with common tuning parameters
	 * 
	 * @param odir
	 * @param run
	 * @throws IOException
	 */
	public static void createSubmitDAGScript(String odir, boolean run) throws IOException {
		String scriptFileName = odir + "submit_DAG.sh";
		FileWriter fw = new FileWriter(scriptFileName);
		fw.write("#!/bin/bash\n");
		fw.write("" + "\n");
		fw.write("if [ -f ~/.bash_profile ]; then" + "\n");
		fw.write("\t. ~/.bash_profile" + "\n");
		fw.write("fi" + "\n");
		fw.write("" + "\n");
		fw.write("cd "+odir+"\n");
		String dagArgs = "-maxidle " + DAGMAN_MAX_IDLE + " -MaxPre " + DAGMAN_MAX_PRE + 
		" -MaxPost " + DAGMAN_MAX_POST + 
		" -OldRescue 0 -AutoRescue 1";
		fw.write("condor_submit_dag " + dagArgs + " main.dag" + "\n");
		fw.close();
		if (run) {
			String outFile = scriptFileName + ".subout";
			String errFile = scriptFileName + ".suberr";
			int retVal = RunScript.runScript(new String[]{"sh", "-c", "sh "+scriptFileName}, outFile, errFile);
			System.out.println("Command executed with status " + retVal);
		}
	}
	
	public void setRequirements(String requirements) {
		this.requirements = requirements;
	}
	
	public String getRequirements() {
		return requirements;
	}
	
	public static void usage() {
		System.err.println("USAGE: HazardDataSetDAGCreator [args] <Input XML> <Curves Per Job> <Calc Dir> <Java Path> <Jar Path>");
		System.err.println("Valid args:");
		System.err.println("\t--reqs <requirements>");
		System.exit(2);
	}
	
	public static void main(String args[]) {
		System.out.println(HazardDataSetDAGCreator.class.getName() + ": starting up");
		if (args.length < 5) {
			usage();
		}
		int counter = 0;
		String reqs = null;
		if (args.length > 5) {
			boolean isArg = true;
			while (isArg) {
				String arg = args[counter++];
				if (arg.startsWith("--reqs")) {
					reqs = args[counter++];
				} else {
					counter--;
					isArg = false;
				}
			}
		}
		if (args.length - counter != 5)
			usage();
		
		String inputFile = args[counter++];
		int curvesPerJob = Integer.parseInt(args[counter++]);
		String calcDir = args[counter++];
		String javaPath = args[counter++];
		String jarPath = args[counter++];
		
		try {
			Document doc = XMLUtils.loadDocument(inputFile);
			CalculationInputsXMLFile inputs = CalculationInputsXMLFile.loadXML(doc);
			
			HazardDataSetDAGCreator dagCreator = new HazardDataSetDAGCreator(inputs, javaPath, jarPath);
			dagCreator.setRequirements(reqs);
			
			File calcDirFile = new File(calcDir);
			
			dagCreator.writeDAG(calcDirFile, curvesPerJob, false);
			
			System.out.println("DONE!");
			
			System.exit(0);
		} catch (MalformedURLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		} catch (DocumentException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		} catch (InvocationTargetException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(1);
		}
	}
}
