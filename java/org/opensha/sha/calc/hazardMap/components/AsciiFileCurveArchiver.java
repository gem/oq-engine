package org.opensha.sha.calc.hazardMap.components;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.text.DecimalFormat;

import org.dom4j.Element;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;

/**
 * This class writes hazard curves to simple output files.
 * 
 * @author kevin
 *
 */
public class AsciiFileCurveArchiver implements CurveResultsArchiver {
	
	public static final String XML_METADATA_NAME = "AsciiFileCurveArchiver";
	
	private String outputDir;
	private boolean binByLat;
	private boolean binByLon;
	
	private static DecimalFormat decimalFormat=new DecimalFormat("0.00##");
	
	/**
	 * 
	 * @param outputDir - directory where curves will be stored
	 * @param binByLat - if true, curves will be put in subdirectories for each
	 * 				latitude value. This prevents directories from getting too large
	 * 				(storing too many files) for big calculatoins 
	 * @param binByLon - same as binByLat but for longitude 
	 * @throws IOException 
	 */
	public AsciiFileCurveArchiver(String outputDir, boolean binByLat, boolean binByLon) throws IOException {
		if (!outputDir.endsWith(File.separator))
			outputDir += File.separator;
		this.binByLat = binByLat;
		this.binByLon = binByLon;
		setOutputDir(outputDir);
		System.out.println("Output Dir: " + outputDir);
	}

	public void archiveCurve(ArbitrarilyDiscretizedFunc curve, CurveMetadata meta) throws IOException {
		String outFileName = getFileName(meta);
		System.out.println("Writing '" + outFileName + "'");
		DiscretizedFunc.writeSimpleFuncFile(curve, outFileName);
	}
	
	private String getFileName(CurveMetadata meta) {
		Location loc = meta.getSite().getLocation();
		String dir = outputDir;
		dir += meta.getShortLabel() + File.separator;
		if (binByLat) {
			dir += loc.getLatitude() + File.separator;
		}
		if (binByLon) {
			dir += loc.getLongitude() + File.separator;
		}
		File dirFile = new File(dir);
		if (!dirFile.exists())
			dirFile.mkdirs();
		return dir + formatLocation(loc) + ".txt";
	}
	
	public String getOutputDir() {
		return outputDir;
	}
	
	public void setOutputDir(String outputDir) throws IOException {
		this.outputDir = outputDir;
		File outputDirFile = new File(outputDir);
		if (!outputDirFile.exists())
			if (!outputDirFile.mkdir())
				System.err.println("WARNING: Output directory could not be created: '" + outputDir + "'");
		else if (!outputDirFile.isDirectory())
			throw new IOException("Output directory already exists and is not a directory: '" + outputDir + "'");
	}
	
	private static String formatLocation(Location loc) {
		return decimalFormat.format(loc.getLatitude()) + "_" + decimalFormat.format(loc.getLongitude());
	}

	public Element toXMLMetadata(Element root) {
		Element el = root.addElement(XML_METADATA_NAME);
		
		el.addAttribute("outputDir", outputDir);
		el.addAttribute("binByLat", binByLat + "");
		el.addAttribute("binByLon", binByLon + "");
		
		return root;
	}
	
	public static AsciiFileCurveArchiver fromXMLMetadata(Element archiverEl) throws IOException {
		String outputDir = archiverEl.attributeValue("outputDir");
		boolean binByLat = Boolean.parseBoolean(archiverEl.attributeValue("binByLat"));
		boolean binByLon = Boolean.parseBoolean(archiverEl.attributeValue("binByLon"));
		
		return new AsciiFileCurveArchiver(outputDir, binByLat, binByLon);
	}

	public boolean isCurveCalculated(CurveMetadata meta, ArbitrarilyDiscretizedFunc xVals) {
		String outFileName = getFileName(meta);
		File file = new File(outFileName);
		if (file.exists()) {
			try {
				DiscretizedFuncAPI func = ArbitrarilyDiscretizedFunc.loadFuncFromSimpleFile(outFileName);
				if (func.getNum() == xVals.getNum()) {
					boolean match = true;
					for (int i=0; i<func.getNum(); i++) {
						if (func.getX(i) != xVals.getX(i)) {
							match = false;
							break;
						}
					}
					return match;
				}
			} catch (Exception e) {}
		}
		return false;
	}

	@Override
	public File getStoreDir() {
		return new File(outputDir);
	}
	
}
