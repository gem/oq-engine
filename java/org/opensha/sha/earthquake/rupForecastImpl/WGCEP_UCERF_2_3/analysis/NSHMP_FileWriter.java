/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UnsegmentedSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults.A_FaultSegmentedSourceGenerator;

/**
 * Write the files to be used by NSHMP.
 * 
 * It creates an instance of UCERF2 and generates a bunch of files that are sent to Golden
 * for NSHMP.  The method writeNSHMP_SrcFiles() accepts a directory name where all the files
 * are generated. 
 * 
 * 
 * @author vipingupta
 *
 */
public class NSHMP_FileWriter {
	private UCERF2 ucerf2;
	
	
	public NSHMP_FileWriter() {
		ucerf2 = new UCERF2();
	}
	
	public NSHMP_FileWriter(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
	}
	
	/**
	 * Make Source files for NSHMP
	 * It makes separate file for each fault for each run.
	 * There are 4 runs.
	 *
	 */
	public void writeNSHMP_SrcFiles(String dirName) {
		File file = new File(dirName);
		if(!file.isDirectory()) file.mkdirs();
		writeNSHMP_SrcFilesForDefModel( dirName, "D2.1");
		writeNSHMP_SrcFilesForDefModel( dirName, "D2.2");
		writeNSHMP_SrcFilesForDefModel( dirName, "D2.3");
		writeNSHMP_SrcFilesForDefModel( dirName, "D2.4");
		writeNSHMP_SrcFilesForDefModel( dirName, "D2.5");
		writeNSHMP_SrcFilesForDefModel( dirName, "D2.6");
	}
	
	/**
	 * Make Source files for NSHMP for a particular deformation model
	 *
	 */
	public void writeNSHMP_SrcFilesForDefModel(String dirName, String defModelName) {

		
		// FOR SEGMENTED MODEL

		// Default parameters
		ucerf2.setParamDefaults();
		ucerf2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		ucerf2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue(defModelName);
		ucerf2.updateForecast();
		writeNSHMP_SegmentedAfaultSrcFile(dirName+"/"+"aFault_MoBal_EllB_"+defModelName);
		// change Mag Area to Hans Bakun
		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		writeNSHMP_SegmentedAfaultSrcFile(dirName+"/"+"aFault_MoBal_HB_"+defModelName);
		// default with High apriori model weight
		ucerf2.setParamDefaults();
		ucerf2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		ucerf2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue(defModelName);
		ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME).setValue(new Double(1e10));
		ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME).setValue(new Double(0));
		ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME).setValue(new Double(0));
		ucerf2.updateForecast();
		writeNSHMP_SegmentedAfaultSrcFile(dirName+"/"+"aFault_aPriori_EllB_"+defModelName);

		// change Mag Area Rel
		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		writeNSHMP_SegmentedAfaultSrcFile(dirName+"/"+"aFault_aPriori_HB_"+defModelName);
		
		// UNSEGMENTED MODELS & B-FAULTS
		ucerf2.setParamDefaults();
		ucerf2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		ucerf2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue(defModelName);
		ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).setValue(UCERF2.UNSEGMENTED_A_FAULT_MODEL);
		ucerf2.updateForecast();
		writeNSHMP_UnsegmentedAfaultSrcFile(dirName+"/"+"aFault_unseg_EllB_"+defModelName);
		writeNSHMP_BfaultSrcFiles(dirName+"/"+"bFault_stitched_EllB_"+defModelName);
		// change Mag Area to Hans Bakun
		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		writeNSHMP_UnsegmentedAfaultSrcFile(dirName+"/"+"aFault_unseg_HB_"+defModelName);
		writeNSHMP_BfaultSrcFiles(dirName+"/"+"bFault_stitched_HB_"+defModelName);
		

		// UNSTITCHED B-FAULTS
		ucerf2.setParamDefaults();
		ucerf2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		ucerf2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue(defModelName);
		ucerf2.getParameter(UCERF2.CONNECT_B_FAULTS_PARAM_NAME).setValue(new Boolean(false));
		ucerf2.updateForecast();
		writeNSHMP_BfaultSrcFiles(dirName+"/"+"bFault_unstitched_EllB_"+defModelName);

		// change Mag Area to Hans Bakun
		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		writeNSHMP_BfaultSrcFiles(dirName+"/"+"bFault_unstitched_HB_"+defModelName);

	}
	
	

	/**
	 * Write a file that has data for each Segmented source for NSHMP with the current parameters
	 * 
	 * @param fileName
	 */
	private void writeNSHMP_SegmentedAfaultSrcFile(String fileNamePrefix) {
		try {
			// Write the adjustable Params
			/*String metadataString="";
			Iterator it = this.adjustableParams.getParametersIterator();
			while(it.hasNext()) 
				metadataString += "# "+((ParameterAPI)it.next()).getMetadataString()+"\n";*/
			// now write all ruptures
			ArrayList aFaultSourceGenerators = this.ucerf2.get_A_FaultSourceGenerators();
			int numSources  = aFaultSourceGenerators.size();	
			FileWriter fw = new FileWriter(fileNamePrefix+".txt");

			for(int iSrc = 0; iSrc<numSources; ++iSrc) {
				String faultName;
				// Segmented source
				A_FaultSegmentedSourceGenerator segmentedSource = (A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(iSrc);
				faultName = segmentedSource.getFaultSegmentData().getFaultName();
//				Commented out:				fw.write(metadataString);
				fw.write(segmentedSource.getNSHMP_SrcFileString());
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Write NSHMP file for Unsegmented A faults (assumes parameters were set and run accordingly)
	 * 
	 * @param fileName
	 */
	private void writeNSHMP_UnsegmentedAfaultSrcFile(String fileName) {
		try {
			ArrayList aFaultSourceGenerators = this.ucerf2.get_A_FaultSourceGenerators();
			// now write all ruptures for A faults
			int numSources  = aFaultSourceGenerators.size();	
			FileWriter fw = new FileWriter(fileName+".txt");
			for(int iSrc = 0; iSrc<numSources; ++iSrc) {
				// unsegmented source
				UnsegmentedSource unsegmentedSource = (UnsegmentedSource)aFaultSourceGenerators.get(iSrc);
				fw.write(unsegmentedSource.getNSHMP_GR_SrcFileString());		
			}
			fw.close();

		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Write NSHMP files for B faults (GR vs Char files)
	 * 
	 * @param fileName
	 */	
	private void writeNSHMP_BfaultSrcFiles(String fileName) {
		try {
			ArrayList<UnsegmentedSource> bFaultSources = this.ucerf2.get_B_FaultSources();
			int numSources  = bFaultSources.size();	
			FileWriter fw = new FileWriter(fileName+"_GR.txt");
			FileWriter fwChar = new FileWriter(fileName+"_Char.txt");
			for(int iSrc = 0; iSrc<numSources; ++iSrc) {
				// unsegmented source
				
				UnsegmentedSource unsegmentedSource = (UnsegmentedSource)bFaultSources.get(iSrc);
				// do not give Creeping Segment to NSHMP as they already have their own file format or it
				if(unsegmentedSource.getFaultSegmentData().getFaultName().equalsIgnoreCase("San Andreas (Creeping Segment)"))
						continue;
				fw.write(unsegmentedSource.getNSHMP_GR_SrcFileString());		
				fwChar.write(unsegmentedSource.getNSHMP_Char_SrcFileString());
			}
			fw.close();
			fwChar.close();

		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	
	public static void main(String[] args) {
		NSHMP_FileWriter nshmpFileWriter = new NSHMP_FileWriter();
		nshmpFileWriter.writeNSHMP_SrcFiles("NSHMP_March25");
	}
	
}
