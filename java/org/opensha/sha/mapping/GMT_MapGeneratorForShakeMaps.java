/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.mapping;

import java.awt.Color;
import java.io.File;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.exceptions.GMT_MapException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.mapping.gmt.GMT_Map;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.mapping.gmt.elements.PSXYPolygon;
import org.opensha.commons.mapping.gmt.elements.PSXYSymbol;
import org.opensha.commons.mapping.gmt.elements.PSXYSymbolSet;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.commons.util.RunScript;
import org.opensha.commons.util.cpt.CPT;
import org.opensha.commons.util.cpt.CPTVal;
import org.opensha.commons.util.cpt.LinearBlender;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

/**
 * <p>Title: GMT_MapGeneratorForShakeMaps</p>
 * <p>Description: This class extends the GMT_MapGenerator to extend the
 * GMT functionality for the shakeMaps.</p>
 * @author : Edward (Ned) Field , Nitin Gupta
 * @dated Dec 31,2003
 */

public class GMT_MapGeneratorForShakeMaps extends GMT_MapGenerator{

	/**
	 * Name of the class
	 */
	protected final static String C = "GMT_MapGeneratorForShakeMaps";
	
	public static final String OPENSHA_HAZUS_SERVLET_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "GMT_HazusMapServlet";

	// for debug purpose
	protected final static boolean D = false;

	private String EQK_RUP_XYZ_FILE_NAME = "eqkRup_data.txt";
	XYZ_DataSetAPI eqkRup_xyzDataSet;

	private String DEFAULT_HAZUS_FILE_PREFIX = "map_hazus";
	private String HAZUS_FILE_PREFIX = DEFAULT_HAZUS_FILE_PREFIX;

	//Defintion of the static String used as the prefixes before the file names for hazus.
	public final static String SA_10 ="sa10";
	public final static String SA_03 ="sa03";
	public final static String PGA ="pga";
	public final static String PGV ="pgv";

	private EqkRupture eqkRup;

	int counter=0;

	//IMT selected
	private String imt;

	// for the rupture surface plotting parameter
	public final static String RUP_PLOT_PARAM_NAME = "Rupture-Surface Plotting";
	private final static String RUP_PLOT_PARAM_PERIMETER = "Draw Perimeter";
	private final static String RUP_PLOT_PARAM_POINTS = "Draw Discrete Points";
	private final static String RUP_PLOT_PARAM_NOTHING = "Draw Nothing";
	private final static String RUP_PLOT_PARAM_INFO = "The hypocenter will also be plotted (as a star) if it has been set" ;
	StringParameter rupPlotParam;

	//creating the parameter to generate the Hazus Shape File
	public final static String HAZUS_SHAPE_PARAM_NAME = "Generate Hazus Shape Files";
	private final static String HAZUS_SHAPE_PARAM_INFO = "This will generate HAZUS shape files";
	BooleanParameter hazusShapeParam;

	public GMT_MapGeneratorForShakeMaps() {

		super();

		StringConstraint rupPlotConstraint = new StringConstraint();
		rupPlotConstraint.addString( RUP_PLOT_PARAM_PERIMETER );
		rupPlotConstraint.addString( RUP_PLOT_PARAM_POINTS );
		rupPlotConstraint.addString( RUP_PLOT_PARAM_NOTHING );
		rupPlotParam = new StringParameter( RUP_PLOT_PARAM_NAME, rupPlotConstraint, RUP_PLOT_PARAM_PERIMETER );
		rupPlotParam.setInfo( RUP_PLOT_PARAM_INFO );

		//creating the Boolean parameter to generate the shape files from the Hazus code
		hazusShapeParam = new BooleanParameter(HAZUS_SHAPE_PARAM_NAME, new Boolean(false));
		hazusShapeParam.setInfo(HAZUS_SHAPE_PARAM_INFO);

		adjustableParams.addParameter(hazusShapeParam);
		adjustableParams.addParameter(rupPlotParam);

	}

	private void setFileNames(String prefix) {
		if(prefix != null) {
			//GMT_SCRIPT_NAME = prefix+"_"+DEFAULT_GMT_SCRIPT_NAME;
			XYZ_FILE_NAME = prefix+"_"+DEFAULT_XYZ_FILE_NAME;
			//METADATA_FILE_NAME = prefix+"_"+DEFAULT_METADATA_FILE_NAME;
			PS_FILE_NAME = prefix+"_"+DEFAULT_PS_FILE_NAME;
			JPG_FILE_NAME = prefix+"_"+DEFAULT_JPG_FILE_NAME;
			PDF_FILE_NAME = prefix+"_"+DEFAULT_PDF_FILE_NAME;
			HAZUS_FILE_PREFIX = prefix+"_"+DEFAULT_HAZUS_FILE_PREFIX;
		}
		else {
			GMT_SCRIPT_NAME = DEFAULT_GMT_SCRIPT_NAME;
			XYZ_FILE_NAME = DEFAULT_XYZ_FILE_NAME;
			METADATA_FILE_NAME = DEFAULT_METADATA_FILE_NAME;
			PS_FILE_NAME = DEFAULT_PS_FILE_NAME;
			JPG_FILE_NAME = DEFAULT_JPG_FILE_NAME;
			PDF_FILE_NAME = DEFAULT_PDF_FILE_NAME;
			HAZUS_FILE_PREFIX = DEFAULT_HAZUS_FILE_PREFIX;
		}
	}


	/**
	 *
	 * @param sa03DataSet
	 * @param sa10DataSet
	 * @param pgaDataSet
	 * @param pgvDataSet
	 * @param eqkRupture
	 * returns the String[] of the image file names
	 */
	public String[] makeHazusFileSetLocally(XYZ_DataSetAPI sa03DataSet,XYZ_DataSetAPI sa10DataSet,
			XYZ_DataSetAPI pgaDataSet,XYZ_DataSetAPI pgvDataSet,
			EqkRupture eqkRupture, String metadata, String dirName)
	throws GMT_MapException{

		//creating the Metadata file in the GMT_MapGenerator
		createMapInfoFile(metadata);

		eqkRup = eqkRupture;

		GMT_PATH="/sw/bin/";
		GS_PATH="/sw/bin/gs";
		PS2PDF_PATH = "/sw/bin/ps2pdf";
		CONVERT_PATH="/sw/bin/convert";

		ArrayList gmtLines = new ArrayList();

		// Do 0.3-sec SA first
		imt="SA";
		SCALE_LABEL = SA_03;
		setFileNames(SCALE_LABEL);
		String sa_03Image = this.JPG_FILE_NAME;
		xyzDataSet = sa03DataSet;
		makeXYZ_File(XYZ_FILE_NAME);
		gmtLines.addAll(getGMT_ScriptLines());

		// Do 1.0-sec SA
		imt="SA";
		SCALE_LABEL = SA_10;
		setFileNames(SCALE_LABEL);
		String sa_10Image = this.JPG_FILE_NAME;
		xyzDataSet = sa10DataSet;
		makeXYZ_File(XYZ_FILE_NAME);
		gmtLines.addAll(getGMT_ScriptLines());

		// PGA
		imt="PGA";
		SCALE_LABEL = PGA;
		setFileNames(SCALE_LABEL);
		String pgaImage = this.JPG_FILE_NAME;
		xyzDataSet = pgaDataSet;
		makeXYZ_File(XYZ_FILE_NAME);
		gmtLines.addAll(getGMT_ScriptLines());

		// Do 0.3-sec SA first
		imt="PGV";
		SCALE_LABEL = PGV;
		setFileNames(SCALE_LABEL);
		String pgvImage = this.JPG_FILE_NAME;
		xyzDataSet = pgvDataSet;
		makeXYZ_File(XYZ_FILE_NAME);
		gmtLines.addAll(getGMT_ScriptLines());

		// make the script
		makeFileFromLines(gmtLines,GMT_SCRIPT_NAME);

		// now run the GMT script file
		String[] command ={"sh","-c","sh "+GMT_SCRIPT_NAME};
		RunScript.runScript(command);
		imgWebAddr = this.JPG_FILE_NAME;

		//gets the all the image names in a String array.
		String img[] = new String[4];
		img[0] = new String(sa_03Image);
		img[1] = new String(sa_10Image);
		img[2] = new String(pgaImage);
		img[3] = new String(pgvImage);

		// set the filenames back to default
		setFileNames(null);
		return img;
	}


	/**
	 *
	 * @param sa03DataSet
	 * @param sa10DataSet
	 * @param pgaDataSet
	 * @param pgvDataSet
	 * @param eqkRupture
	 * @return - the String[] of web addresses(URL) where the images files are located
	 */
	public String[] makeHazusFileSetUsingServlet(XYZ_DataSetAPI sa03DataSet,XYZ_DataSetAPI sa10DataSet,
			XYZ_DataSetAPI pgaDataSet,XYZ_DataSetAPI pgvDataSet,
			EqkRupture eqkRupture,String metadata,String dirName)
	throws GMT_MapException{
		eqkRup = eqkRupture;

		GMT_PATH="/opt/install/gmt/bin/";
		GS_PATH="/usr/local/bin/gs";
		PS2PDF_PATH = "/usr/local/bin/ps2pdf";
		CONVERT_PATH="/usr/bin/convert";
		
		GMT_Map maps[] = new GMT_Map[4];

		// Do 0.3-sec SA first
		imt="SA";
		SCALE_LABEL = SA_03;
		xyzDataSet = sa03DataSet;
		setFileNames(SCALE_LABEL);
		maps[0] = getGMTMapSpecification(xyzDataSet);
		String sa_03Image = this.JPG_FILE_NAME;

		// Do 1.0-sec SA
		imt="SA";
		SCALE_LABEL = SA_10;
		xyzDataSet = sa10DataSet;
		setFileNames(SCALE_LABEL);
		maps[1] = getGMTMapSpecification(xyzDataSet);
		String sa_10Image = this.JPG_FILE_NAME;

		// PGA
		imt="PGA";
		SCALE_LABEL = PGA;
		xyzDataSet = pgaDataSet;
		setFileNames(SCALE_LABEL);
		String pgaImage = this.JPG_FILE_NAME;
		maps[2] = getGMTMapSpecification(xyzDataSet);

		// Do 0.3-sec SA first
		imt="PGV";
		SCALE_LABEL = PGV;
		xyzDataSet = pgvDataSet;
		setFileNames(SCALE_LABEL);
		String pgvImage = this.JPG_FILE_NAME;
		maps[3] = getGMTMapSpecification(xyzDataSet);


		String img[] = new String[4];
		try{
			imgWebAddr = this.openServletConnection(sa03DataSet, sa10DataSet, pgaDataSet,
					pgvDataSet, maps, metadata, dirName);
			img[0] = new String(imgWebAddr + sa_03Image);
			img[1] = new String(imgWebAddr + sa_10Image);
			img[2] = new String(imgWebAddr + pgaImage);
			img[3] = new String(imgWebAddr + pgvImage);
		}catch(RuntimeException e){
			e.printStackTrace();
			throw new RuntimeException(e.getMessage());
		}

		// set the filenames back to default
		setFileNames(null);
		return img;
	}


	/**
	 * sets up the connection with the servlet on the server (gravity.usc.edu)
	 * @param sa03_xyzDataVals : XYZ data for the SA-0.3sec
	 * @param sa10_xyzDataVals : XYZ data for the SA-1.0sec
	 * @param pga_xyzDataVals  : XYZ data for the PGA
	 * @param pgv_xyzDataVals  : XYZ data for the PGV
	 * @param gmtFileLines     : Script lines to be executed on the server
	 * @param metadataLines    : MetadataLines
	 * @returns the webaddress of the Directory as the link to where all the
	 * output files are generated
	 * @throws RuntimeException
	 */
	protected String openServletConnection(XYZ_DataSetAPI sa03_xyzDataVals,
			XYZ_DataSetAPI sa10_xyzDataVals, XYZ_DataSetAPI pga_xyzDataVals,
			XYZ_DataSetAPI pgv_xyzDataVals, GMT_Map maps[],String metadata,String dirName) throws RuntimeException{

		String webaddr=null;
		try{

			if(D) System.out.println("starting to make connection with servlet");
			URL gmtMapServlet = new URL(OPENSHA_HAZUS_SERVLET_URL);


			URLConnection servletConnection = gmtMapServlet.openConnection();
			if(D) System.out.println("connection established");

			// inform the connection that we will send output and accept input
			servletConnection.setDoInput(true);
			servletConnection.setDoOutput(true);

			// Don't use a cached version of URL connection.
			servletConnection.setUseCaches (false);
			servletConnection.setDefaultUseCaches (false);
			// Specify the content type that we will send binary data
			servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

			ObjectOutputStream outputToServlet = new
			ObjectOutputStream(servletConnection.getOutputStream());

			//sending the directory name to the servlet
			outputToServlet.writeObject(dirName);

			//sending the map specification
			outputToServlet.writeObject(maps);

			//sending the contents of the Metadata file to the server.
			outputToServlet.writeObject(metadata);

			//sending the name of the MetadataFile to the server.
			outputToServlet.writeObject(DEFAULT_METADATA_FILE_NAME);

			outputToServlet.flush();
			outputToServlet.close();

			// Receive the "actual webaddress of all the gmt related files"
			// from the servlet after it has received all the data
			ObjectInputStream inputToServlet = new
			ObjectInputStream(servletConnection.getInputStream());

			Object messageFromServlet = inputToServlet.readObject();
			inputToServlet.close();
			if(messageFromServlet instanceof String){
				webaddr = (String) messageFromServlet;
				if (D) System.out.println("Receiving the Input from the Servlet:" +
						webaddr);
			}
			else
				throw (RuntimeException)messageFromServlet;
		}catch (Exception e) {
			e.printStackTrace();
			throw new RuntimeException("Server is down , please try again later");
		}
		return webaddr;
	}




	/**
	 * Makes scenarioshake maps locally using the GMT on the users own computer
	 * @param xyzDataSet: XYZ Data
	 * @param eqkRup : EarthRupture Object
	 * @param hypLoc :Hypocenter Location
	 * @param imtString - the IMT string for labeling and filenames
	 * @return
	 */
	public String makeMapLocally(XYZ_DataSetAPI xyzDataSet, EqkRupture eqkRupture,
			String imtString, String metadata,String directoryName)
	throws GMT_MapException{
		eqkRup = eqkRupture;
		imt = imtString;

		// make name change each time so viewing files doesn't get screwed up
		//JPG_FILE_NAME = "map"+counter+".jpg";

		// Add time stamp to script name (for when we want to save many scripts locally)
		//    GMT_SCRIPT_NAME=DEFAULT_GMT_SCRIPT_NAME.substring(0,DEFAULT_GMT_SCRIPT_NAME.indexOf("."))+System.currentTimeMillis()+".txt";

		String jpgFileName = super.makeMapLocally(xyzDataSet,imtString,metadata,directoryName);
		String dirName =null;
		String tempScript = null;

		// Make a directory and move all the files into it
		if(directoryName !=null){
			File f = new File(directoryName);
			int fileCounter =1;
			//checking if the directory already exists then add
			while(f.exists()){
				String tempDirName = directoryName+fileCounter;
				f = new File(tempDirName);
				++fileCounter;
			}
			dirName = "UserShakeMaps_"+f.getName();
			tempScript = "temp"+f.getName();
		}
		else{
			dirName = "UserShakeMaps_"+System.currentTimeMillis();
			tempScript = "temp"+System.currentTimeMillis();
		}
		ArrayList scriptLines = new ArrayList();
		String commandLine = COMMAND_PATH+"mkdir "+dirName;
		scriptLines.add(commandLine+"\n");
		commandLine = COMMAND_PATH+"mv "+GMT_SCRIPT_NAME+" "+XYZ_FILE_NAME+" "+
		METADATA_FILE_NAME+" "+PS_FILE_NAME+" "+JPG_FILE_NAME+" "+
		PDF_FILE_NAME+"  "+
		HAZUS_FILE_PREFIX+".shp "+HAZUS_FILE_PREFIX+".shx "+
		HAZUS_FILE_PREFIX+".dbf "+ dirName;
		scriptLines.add(commandLine+"\n");
		commandLine = COMMAND_PATH+"rm "+tempScript;
		scriptLines.add(commandLine+"\n");
		makeFileFromLines(scriptLines,tempScript);
		String[] command ={"sh","-c","sh "+tempScript};
		RunScript.runScript(command);

		return dirName + "/" + jpgFileName;
	}

	/**
	 * Makes scenarioshake maps using the GMT on the gravity.usc.edu server(Linux server).
	 * Implemented as the servlet, using which we can actual java serialized object.
	 * @param xyzDataSet: XYZ Data
	 * @param eqkRup : EarthRupture Object
	 * @param hypLoc : Hypocenter Location
	 * @param imtString - the IMT string for labeling and filenames
	 * @return: URL to the image
	 */
	public String makeMapUsingServlet(XYZ_DataSetAPI xyzDataSet,
			EqkRupture eqkRupture,
			String imtString,String metadata, String dirName) throws
			GMT_MapException,RuntimeException{
		eqkRup = eqkRupture;
		imt = imtString;
		return super.makeMapUsingServlet(xyzDataSet, imtString, metadata, dirName);
	}

	/**
	 * Makes scenarioshake maps using the GMT on the gravity.usc.edu server(Linux server).
	 * Implemented as the webservice, using which we can send files as the attachment.
	 * @param xyzDataSet: XYZ Data
	 * @param eqkRup : EarthRupture Object
	 * @param hypLoc :Hypocenter Location
	 * @param imtString - the IMT string for labeling and filenames
	 * @return: URL to the image
	 */
	public String makeMapUsingWebServer(XYZ_DataSetAPI xyzDataSet,
			EqkRupture eqkRupture,
			String imtString, String metadata) throws
			GMT_MapException {
		eqkRup = eqkRupture;
		imt = imtString;
		return super.makeMapUsingWebServer(xyzDataSet, imtString, metadata);
	}

	public static void addHAZUS_Lines(ArrayList<String> gmtCommandLines, GMT_Map map, String imt, String hazusPrefix) {
		// stop here is log was selected
		if(map.isLogPlot())
			throw new RuntimeException("You cannot make Hazus Shapefiles with log-plot selected!");

		String HAZUS_SHAPE_FILE_GENERATOR = "/usr/local/tomcat/default/webapps/OpenSHA/hazus/contour";
		// Get the limits and discretization of the map
		double minLat = map.getRegion().getMinLat();
		double maxTempLat = map.getRegion().getMaxLat();
		double minLon = map.getRegion().getMinLon();
		double maxTempLon = map.getRegion().getMaxLon();
		double gridSpacing = map.getGriddedDataInc();

		// adjust the max lat and lon to be an exact increment (needed for xyz2grd)
		double maxLat = Math.rint(((maxTempLat-minLat)/gridSpacing))*gridSpacing +minLat;
		double maxLon = Math.rint(((maxTempLon-minLon)/gridSpacing))*gridSpacing +minLon;

		//redefing the region for proper discretization of the region required by the GMT
		String region = " -R" + minLon + "/" + maxLon + "/" + minLat + "/" + maxLat+" ";
//		String imt = map.get
		String commandLine;
		//if the selected IMT is SA
		if(imt.equals(SA_Param.NAME)){
			commandLine = "${GMT_PATH}xyz2grd "+map.getXyzFileName()+" -Gtemp.grd=1 "+
			"-I"+gridSpacing+region+" -D/degree/degree/amp/=/=/= -: -H0 -V";
			gmtCommandLines.add(commandLine+"\n");
			commandLine = HAZUS_SHAPE_FILE_GENERATOR+" -g temp.grd -C 0.04 -f 0.02 -Z 1.0 -T4 -o "+hazusPrefix;
			gmtCommandLines.add(commandLine+"\n");
		}
		//if the selected IMT is PGA
		else if(imt.equals(PGA_Param.NAME)){
			commandLine = "${GMT_PATH}xyz2grd "+map.getXyzFileName()+" -Gtemp.grd=1 "+
			"-I"+gridSpacing+region+" -D/degree/degree/amp/=/=/= -: -H0 -V";
			gmtCommandLines.add(commandLine+"\n");
			commandLine = HAZUS_SHAPE_FILE_GENERATOR+" -g temp.grd -C 0.04 -f 0.02 -Z 1.0 -T4 -o "+hazusPrefix;
			gmtCommandLines.add(commandLine+"\n");
		}
		//if the selected IMT is PGV
		else if(imt.equals(PGV_Param.NAME)){
			commandLine = "${GMT_PATH}xyz2grd "+map.getXyzFileName()+" -Gtemp.grd=1 "+
			"-I"+gridSpacing+region+" -D/degree/degree/amp/=/=/= -: -H0 -V";
			gmtCommandLines.add(commandLine+"\n");
			commandLine = HAZUS_SHAPE_FILE_GENERATOR+" -g temp.grd -C 4.0 -f 2.0 -Z 0.3937 -T4 -o "+hazusPrefix;
			gmtCommandLines.add(commandLine+"\n");
		}
		else
			throw new RuntimeException("IMT not supported to generate Shape File");
		commandLine = COMMAND_PATH+"rm temp.grd";
		gmtCommandLines.add(commandLine+"\n");
	}

	/**
	 * Function adds script lines  to generate Hazus Shape files if that option has been selected.
	 * @param gmtCommandLines : ArrayList to store the command line
	 */
	protected void addFinalGMT_ScriptLines(ArrayList gmtCommandLines){

		boolean doHaveToGenerateShapeFile = ((Boolean)hazusShapeParam.getValue()).booleanValue();
		if(doHaveToGenerateShapeFile){
			// stop here is log was selected
			boolean logPlotCheck = ((Boolean)logPlotParam.getValue()).booleanValue();
			if(((Boolean)logPlotParam.getValue()).booleanValue())
				throw new RuntimeException("You cannot make Hazus Shapefiles with log-plot selected!");

			String HAZUS_SHAPE_FILE_GENERATOR = "/usr/scec/hazus/shapefilegenerator/contour";
			// Get the limits and discretization of the map
			double minLat = ((Double)adjustableParams.getParameter(MIN_LAT_PARAM_NAME).getValue()).doubleValue();
			double maxTempLat = ((Double)adjustableParams.getParameter(MAX_LAT_PARAM_NAME).getValue()).doubleValue();
			double minLon = ((Double)adjustableParams.getParameter(MIN_LON_PARAM_NAME).getValue()).doubleValue();
			double maxTempLon = ((Double)adjustableParams.getParameter(MAX_LON_PARAM_NAME).getValue()).doubleValue();
			double gridSpacing = ((Double)adjustableParams.getParameter(GRID_SPACING_PARAM_NAME).getValue()).doubleValue();

			// adjust the max lat and lon to be an exact increment (needed for xyz2grd)
			double maxLat = Math.rint(((maxTempLat-minLat)/gridSpacing))*gridSpacing +minLat;
			double maxLon = Math.rint(((maxTempLon-minLon)/gridSpacing))*gridSpacing +minLon;

			//redefing the region for proper discretization of the region required by the GMT
			region = " -R" + minLon + "/" + maxLon + "/" + minLat + "/" + maxLat+" ";
			String commandLine;
			//if the selected IMT is SA
			if(imt.equals(SA_Param.NAME)){
				commandLine = GMT_PATH +"xyz2grd "+XYZ_FILE_NAME+" -Gtemp.grd=1 "+
				"-I"+gridSpacing+region+" -D/degree/degree/amp/=/=/= -: -H0 -V";
				gmtCommandLines.add(commandLine+"\n");
				commandLine = HAZUS_SHAPE_FILE_GENERATOR+" -g temp.grd -C 0.04 -f 0.02 -Z 1.0 -T4 -o "+HAZUS_FILE_PREFIX;
				gmtCommandLines.add(commandLine+"\n");
			}
			//if the selected IMT is PGA
			else if(imt.equals(PGA_Param.NAME)){
				commandLine = GMT_PATH +"xyz2grd "+XYZ_FILE_NAME+" -Gtemp.grd=1 "+
				"-I"+gridSpacing+region+" -D/degree/degree/amp/=/=/= -: -H0 -V";
				gmtCommandLines.add(commandLine+"\n");
				commandLine = HAZUS_SHAPE_FILE_GENERATOR+" -g temp.grd -C 0.04 -f 0.02 -Z 1.0 -T4 -o "+HAZUS_FILE_PREFIX;
				gmtCommandLines.add(commandLine+"\n");
			}
			//if the selected IMT is PGV
			else if(imt.equals(PGV_Param.NAME)){
				commandLine = GMT_PATH +"xyz2grd "+XYZ_FILE_NAME+" -Gtemp.grd=1 "+
				"-I"+gridSpacing+region+" -D/degree/degree/amp/=/=/= -: -H0 -V";
				gmtCommandLines.add(commandLine+"\n");
				commandLine = HAZUS_SHAPE_FILE_GENERATOR+" -g temp.grd -C 4.0 -f 2.0 -Z 0.3937 -T4 -o "+HAZUS_FILE_PREFIX;
				gmtCommandLines.add(commandLine+"\n");
			}
			else
				throw new RuntimeException("IMT not supported to generate Shape File");
			commandLine = COMMAND_PATH+"rm temp.grd";
			gmtCommandLines.add(commandLine+"\n");
		}
		/*
    // TEMPORARY -- copy it to a directory for convenience
    String commandLine = COMMAND_PATH+"mkdir "+imt;
    gmtCommandLines.add(commandLine+"\n");
    commandLine = COMMAND_PATH+"cp "+JPG_FILE_NAME+" "+imt;
    gmtCommandLines.add(commandLine+"\n");
    commandLine = COMMAND_PATH+"mv map.ps xyz_data.txt map_info.txt "+gmtFileName+" map_info "+imt;
    gmtCommandLines.add(commandLine+"\n");
    commandLine = COMMAND_PATH+"mv "+imt+".dbf "+imt+".shp "+imt+".shx " + imt;
    gmtCommandLines.add(commandLine+"\n");
		 */
	}

	@Override
	public GMT_Map getGMTMapSpecification(XYZ_DataSetAPI xyzData) {
		GMT_Map map =  super.getGMTMapSpecification(xyzData);
		
		String rupPlot = rupPlotParam.getValue();

		if(!rupPlot.equals(RUP_PLOT_PARAM_NOTHING)) {

			// Get the surface and associated info
			EvenlyGriddedSurfaceAPI surface = eqkRup.getRuptureSurface();
			Location loc;
			int rows = surface.getNumRows();
			int cols = surface.getNumCols();
			if(D) System.out.println(C+" rows, cols: "+rows+", "+cols);
			int c, r;

			if(rupPlot.equals(RUP_PLOT_PARAM_PERIMETER)) {
				//  This draws separate segments between each neighboring point
				double dMin = surface.getLocation(0,0).getDepth();
				double dMax = surface.getLocation(surface.getNumRows()-1,0).getDepth();
				double maxShade = 235; // up to 255
				double minShade = 20; // as low os 0
				int shade;
				Location lastLoc = surface.getLocation(0,0);

				if(eqkRup.getRuptureSurface().getAveDip() < 90) { // do only if not vertically dipping

					// get points down the far side
					c = cols-1;
					lastLoc = surface.getLocation(0,c);
					for(r=1;r<rows;r++) {
						if(D) System.out.println(C+" row, col: "+r+", "+c);
						shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
						loc = surface.getLocation(r,c);
						PSXYPolygon poly = new PSXYPolygon(lastLoc, loc);
						Color color = new Color(shade, shade, shade);
						poly.setPenColor(color);
						poly.setPenWidth(8);
						map.addPolys(poly);
						lastLoc = loc;
					}
					// get points along the bottom
					r=rows-1;
					for(c=cols-2;c>=0;c--) {
						if(D) System.out.println(C+" row, col: "+r+", "+c);
						shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
						loc = surface.getLocation(r,c);
						PSXYPolygon poly = new PSXYPolygon(lastLoc, loc);
						Color color = new Color(shade, shade, shade);
						poly.setPenColor(color);
						poly.setPenWidth(8);
						map.addPolys(poly);
						lastLoc = loc;
					}
					// get points up the side
					c=0;
					for(r=rows-2;r>=0;r--) {
						if(D) System.out.println(C+" row, col: "+r+", "+c);
						shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
						loc = surface.getLocation(r,c);
						PSXYPolygon poly = new PSXYPolygon(lastLoc, loc);
						Color color = new Color(shade, shade, shade);
						poly.setPenColor(color);
						poly.setPenWidth(8);
						map.addPolys(poly);
						lastLoc = loc;
					}
				}
				// get points along the top - do this last so vertical faults have the shade of the top
				r=0;
				for(c=1;c<cols;c++) {
					if(D) System.out.println(C+" row, col: "+r+", "+c);
					shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
					loc = surface.getLocation(r,c);
					PSXYPolygon poly = new PSXYPolygon(lastLoc, loc);
					Color color = new Color(shade, shade, shade);
					poly.setPenColor(color);
					poly.setPenWidth(8);
					map.addPolys(poly);
					lastLoc = loc;
				}

//				// plot the rupture surface points
//				commandLine = GMT_PATH+"psxy "+ EQK_RUP_XYZ_FILE_NAME + region +
//				projWdth +" -K -O -M >> " + PS_FILE_NAME;
//				gmtLines.add(commandLine+"\n");
//				gmtLines.add(COMMAND_PATH+"rm "+EQK_RUP_XYZ_FILE_NAME+"\n");
			} else {
				// Plot the discrete surface points
				String gmtSymbol = " c0.04i";    // draw a circles of 0.04 inch diameter
				// get points along the top
				
//				LinearBlender blend = new LinearBlender();
				Color bigColor = new Color(20, 20, 20);
				Color smallColor = new Color(235, 235, 235);
				float dep1 = (float)surface.getLocation(0,0).getDepth();
				float dep2 = (float)surface.getLocation(surface.getNumRows()-1,0).getDepth();
				CPT cpt = new CPT();
				cpt.setCPTVal(new CPTVal(dep1, smallColor, dep2, bigColor));
				PSXYSymbolSet symbols = new PSXYSymbolSet();
				symbols.setCpt(cpt);
				for(r=surface.getNumRows()-1;r>=0;r--) {   // reverse order so upper points plot over lower points
					for(c=0;c<surface.getNumCols()-1;c++) {
						loc = surface.getLocation(r,c);
						DataPoint2D pt = new DataPoint2D(loc.getLongitude(), loc.getLatitude());
						PSXYSymbol sym = new PSXYSymbol(pt, PSXYSymbol.Symbol.CIRCLE, 0.04);
						symbols.addSymbol(sym, loc.getDepth());
					}
				}
				map.setSymbolSet(symbols);
				
//				// make the file in the script:
//				gmtLines.add(COMMAND_PATH+"cat << END > "+EQK_RUP_XYZ_FILE_NAME);
//				Iterator it = fileLines.iterator();
//				while(it.hasNext()) gmtLines.add((String)it.next());
//				gmtLines.add("END\n");
//
//				// make the cpt file for the fault points
//				
//				commandLine = COMMAND_PATH+"cat << END > temp_rup_cpt\n"+
//				(float)dep1+" 235 235 253 "+(float)dep2+" 20 20 20\n"+
//				"F 235 235 235\nB 20 20 20\nEND";
//				gmtLines.add(commandLine+"\n");
//
//				// plot the rupture surface points
//				commandLine = GMT_PATH+"psxy "+ EQK_RUP_XYZ_FILE_NAME + region +
//				projWdth +" -K -O -S -Ctemp_rup_cpt >> " + PS_FILE_NAME;
//				gmtLines.add(commandLine+"\n");
//				gmtLines.add(COMMAND_PATH+"rm temp_rup_cpt "+EQK_RUP_XYZ_FILE_NAME+"\n");
			}
//
//
//			// add hypocenter location if it's not null - the data files is generated by the script
//			// this has two data lines because GMT needs at least two lines in an XYZ file
//			loc = eqkRup.getHypocenterLocation();
//			if(loc != null) {
//				commandLine = COMMAND_PATH+"cat << END > temp_hyp\n"+
//				(float)loc.getLongitude()+"  "+(float)loc.getLatitude()+"  "+(float)loc.getDepth()+"\n"+
//				(float)loc.getLongitude()+"  "+(float)loc.getLatitude()+"  "+(float)loc.getDepth()+"\n"+
//				"END";
//				gmtLines.add(commandLine+"\n");
//				commandLine = GMT_PATH+"psxy temp_hyp "+region+
//				projWdth +" -K -O -Sa0.4i -W8/0/0/0 >> " + PS_FILE_NAME;
//				gmtLines.add(commandLine+"\n");
//				gmtLines.add(COMMAND_PATH+"rm temp_hyp\n");
		}
		
		return map;
	}

	/**
	 * This method adds intermediate script commands to plot the earthquake rupture and hypocenter.
	 */
	protected void addIntermediateGMT_ScriptLines(ArrayList gmtLines) {

		String rupPlot = (String) rupPlotParam.getValue();

		if(!rupPlot.equals(RUP_PLOT_PARAM_NOTHING)) {

			String commandLine;

			// Get the surface and associated info
			EvenlyGriddedSurfaceAPI surface = eqkRup.getRuptureSurface();
			ArrayList fileLines = new ArrayList();
			Location loc;
			int rows = surface.getNumRows();
			int cols = surface.getNumCols();
			if(D) System.out.println(C+" rows, cols: "+rows+", "+cols);
			int c, r;

			if(rupPlot.equals(RUP_PLOT_PARAM_PERIMETER)) {
				//  This draws separate segments between each neighboring point
				double dMin = surface.getLocation(0,0).getDepth();
				double dMax = surface.getLocation(surface.getNumRows()-1,0).getDepth();
				double maxShade = 235; // up to 255
				double minShade = 20; // as low os 0
				int shade;
				Location lastLoc = surface.getLocation(0,0);

				if(eqkRup.getRuptureSurface().getAveDip() < 90) { // do only if not vertically dipping

					// get points down the far side
					c = cols-1;
					lastLoc = surface.getLocation(0,c);
					for(r=1;r<rows;r++) {
						if(D) System.out.println(C+" row, col: "+r+", "+c);
						shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
						fileLines.add(new String(">  -W8/"+shade+"/"+shade+"/"+shade));
						fileLines.add(new String((float)lastLoc.getLongitude()+"  "+
								(float)lastLoc.getLatitude()));
						loc = surface.getLocation(r,c);
						fileLines.add(new String((float)loc.getLongitude()+"  "+
								(float)loc.getLatitude()));
						lastLoc = loc;
					}
					// get points along the bottom
					r=rows-1;
					for(c=cols-2;c>=0;c--) {
						if(D) System.out.println(C+" row, col: "+r+", "+c);
						shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
						fileLines.add(new String(">  -W8/"+shade+"/"+shade+"/"+shade));
						fileLines.add(new String((float)lastLoc.getLongitude()+"  "+
								(float)lastLoc.getLatitude()));
						loc = surface.getLocation(r,c);
						fileLines.add(new String((float)loc.getLongitude()+"  "+
								(float)loc.getLatitude()));
						lastLoc = loc;
					}
					// get points up the side
					c=0;
					for(r=rows-2;r>=0;r--) {
						if(D) System.out.println(C+" row, col: "+r+", "+c);
						shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
						fileLines.add(new String(">  -W8/"+shade+"/"+shade+"/"+shade));
						fileLines.add(new String((float)lastLoc.getLongitude()+"  "+
								(float)lastLoc.getLatitude()));
						loc = surface.getLocation(r,c);
						fileLines.add(new String((float)loc.getLongitude()+"  "+
								(float)loc.getLatitude()));
						lastLoc = loc;
					}
				}
				// get points along the top - do this last so vertical faults have the shade of the top
				r=0;
				for(c=1;c<cols;c++) {
					if(D) System.out.println(C+" row, col: "+r+", "+c);
					shade = 20 + (int)((maxShade-minShade)*(dMax - lastLoc.getDepth())/(dMax-dMin));
					fileLines.add(new String(">  -W8/"+shade+"/"+shade+"/"+shade));
					fileLines.add(new String((float)lastLoc.getLongitude()+"  "+
							(float)lastLoc.getLatitude()));
					loc = surface.getLocation(r,c);
					fileLines.add(new String((float)loc.getLongitude()+"  "+
							(float)loc.getLatitude()));
					lastLoc = loc;
				}

				// make the data file in the script:
				gmtLines.add(COMMAND_PATH+"cat << END > "+EQK_RUP_XYZ_FILE_NAME);
				Iterator it = fileLines.iterator();
				while(it.hasNext()) {
					gmtLines.add((String)it.next());
				}
				gmtLines.add("END\n");

				// plot the rupture surface points
				commandLine = GMT_PATH+"psxy "+ EQK_RUP_XYZ_FILE_NAME + region +
				projWdth +" -K -O -M >> " + PS_FILE_NAME;
				gmtLines.add(commandLine+"\n");
				gmtLines.add(COMMAND_PATH+"rm "+EQK_RUP_XYZ_FILE_NAME+"\n");
			}
			else {
				// Plot the discrete surface points
				String gmtSymbol = " c0.04i";    // draw a circles of 0.04 inch diameter
				// get points along the top

				for(r=surface.getNumRows()-1;r>=0;r--) {   // reverse order so upper points plot over lower points
					for(c=0;c<surface.getNumCols()-1;c++) {
						loc = surface.getLocation(r,c);
						fileLines.add(new String((float)loc.getLongitude()+"  "+
								(float)loc.getLatitude()+"  "+
								(float)loc.getDepth()+gmtSymbol));
					}
				}

				// make the file in the script:
				gmtLines.add(COMMAND_PATH+"cat << END > "+EQK_RUP_XYZ_FILE_NAME);
				Iterator it = fileLines.iterator();
				while(it.hasNext()) gmtLines.add((String)it.next());
				gmtLines.add("END\n");

				// make the cpt file for the fault points
				double dep1 = surface.getLocation(0,0).getDepth();
				double dep2 = surface.getLocation(surface.getNumRows()-1,0).getDepth();
				commandLine = COMMAND_PATH+"cat << END > temp_rup_cpt\n"+
				(float)dep1+" 235 235 253 "+(float)dep2+" 20 20 20\n"+
				"F 235 235 235\nB 20 20 20\nEND";
				gmtLines.add(commandLine+"\n");

				// plot the rupture surface points
				commandLine = GMT_PATH+"psxy "+ EQK_RUP_XYZ_FILE_NAME + region +
				projWdth +" -K -O -S -Ctemp_rup_cpt >> " + PS_FILE_NAME;
				gmtLines.add(commandLine+"\n");
				gmtLines.add(COMMAND_PATH+"rm temp_rup_cpt "+EQK_RUP_XYZ_FILE_NAME+"\n");
			}


			// add hypocenter location if it's not null - the data files is generated by the script
			// this has two data lines because GMT needs at least two lines in an XYZ file
			loc = eqkRup.getHypocenterLocation();
			if(loc != null) {
				commandLine = COMMAND_PATH+"cat << END > temp_hyp\n"+
				(float)loc.getLongitude()+"  "+(float)loc.getLatitude()+"  "+(float)loc.getDepth()+"\n"+
				(float)loc.getLongitude()+"  "+(float)loc.getLatitude()+"  "+(float)loc.getDepth()+"\n"+
				"END";
				gmtLines.add(commandLine+"\n");
				commandLine = GMT_PATH+"psxy temp_hyp "+region+
				projWdth +" -K -O -Sa0.4i -W8/0/0/0 >> " + PS_FILE_NAME;
				gmtLines.add(commandLine+"\n");
				gmtLines.add(COMMAND_PATH+"rm temp_hyp\n");
			}
		}
	}
}
