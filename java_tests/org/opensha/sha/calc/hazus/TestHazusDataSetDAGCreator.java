package org.opensha.sha.calc.hazus;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.gridComputing.condor.SubmitScript.Universe;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.calc.hazardMap.components.CalculationInputsXMLFile;
import org.opensha.sha.calc.hazardMap.dagGen.TestHazardDataSetDAGCreator;
import org.opensha.sha.calc.hazus.parallel.HazusDataSetDAGCreator;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

public class TestHazusDataSetDAGCreator extends TestHazardDataSetDAGCreator {

	@Override
	public void testDAGCreation() throws IOException {
		while (imrMaps.size() > 1) {
			imrMaps.remove(imrMaps.size()-1);
		}
		calcSettings.setXValues(null);
		IMT_Info imtInfo = new IMT_Info();
		
		calcSettings.setXValues(PGA_Param.NAME, imtInfo.getDefaultHazardCurve(PGA_Param.NAME));
		calcSettings.setXValues(PGV_Param.NAME, imtInfo.getDefaultHazardCurve(PGV_Param.NAME));
		calcSettings.setXValues(SA_Param.NAME, imtInfo.getDefaultHazardCurve(SA_Param.NAME));
		
		CalculationInputsXMLFile inputs = new CalculationInputsXMLFile(erf, imrMaps, sites, calcSettings, archiver);
		
		XMLUtils.writeObjectToXMLAsRoot(inputs, tempDir.getAbsolutePath() + File.separator + "inputs.xml");
		
		String javaExec = "/usr/bin/java";
		String pwd = System.getProperty("user.dir");
		String jarFile = pwd + File.separator + "dist" + File.separator + "OpenSHA_complete.jar";
		File jarFileFile = new File(jarFile);
		if (!jarFileFile.exists())
			throw new FileNotFoundException("Jar file 'OpenSHA_complete.jar' doesn't exist..." +
					"run ant/CompleteJar.xml to build this jar");
		System.out.println("Jar file: " + jarFile);
		
		HazusDataSetDAGCreator dagCreator;
		try {
			dagCreator = new HazusDataSetDAGCreator(inputs, javaExec, jarFile,
					(int)erf.getTimeSpan().getDuration(TimeSpan.YEARS), region);
		} catch (InvocationTargetException e) {
			throw new RuntimeException(e);
		}
		
		dagCreator.setUniverse(Universe.SCHEDULER);
		dagCreator.writeDAG(tempDir, 100, false);
	}

}
