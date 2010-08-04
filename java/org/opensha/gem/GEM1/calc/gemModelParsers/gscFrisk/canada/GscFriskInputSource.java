package org.opensha.gem.GEM1.calc.gemModelParsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class GscFriskInputSource {

	String name; // 			L1			: Source name
	int geomNum; //				L2			: Number of geometries
	String geomName[]; //		L1 geom		: Geometry name
	double geomWei[]; // 		L2 geom 	: Weight of this geometry
	String geomTyp[]; //		L3 geom		: Source typology
	double geomDepth[][]; //	L4 geom		: Depths (in case of area sources)
	double geomDip1[][]; //		L4 geom	F	: Dip (just in case of faults)
	double geomDip2[][]; //		L4 geom	F	: Dip (just in case of faults)
	double geomZ1[][]; //		L4 geom	F	: Depth (just in case of faults)
	double geomZ2[][]; //		L4 geom	F	: Depth (just in case of faults)
	double geomZ3[][]; //		L4 geom	F	: Depth (just in case of faults)
	double rupLenPar[][]; //	L5 geom F   : Rupture-length equation parameters (a,b,sig)
	int numPnt[]; // 			L1 geom coo : Number of points used to describe the source geometry 
	double mMin[]; //			L1 geom sei : Minimum magnitude
	double mMax[][]; //			L2 geom sei : Maximum magnitude values
	int mfdDist[]; //			L3 geom sei : Type of MFD: 1-truncated GR 2-Char model (only faults)
	double nu[][]; //			L4 geom sei : Rate of exceedance of mMin in the truncated GR relationship 
	double beta[][]; // 		L4 geom sei : Beta of truncated GR relationship
	
	ArrayList<LocationList> coords = new ArrayList<LocationList>(); //   L2 geom coo : Points coordinates (gem,<lon,lat>,idx)
	
	// Used to initialize variables - Not best solution
	static int NCOMML = 3;
	
	/**
	 * 
	 * @param input
	 * @throws IOException
	 */
	public GscFriskInputSource(BufferedReader input, GscFriskInputAlternative alt, boolean
			skipComm) throws IOException {
		
		// General variables
		int i;
		int j;
		String[] strarr;
		String line;
		double lon = 0;
		double lat = 0;
	
		// Define patterns and matchers
		Pattern INTNUM     = Pattern.compile("\\d+");
		Pattern FLOATNUM   = Pattern.compile("(\\+|-)*\\d+\\.*(\\d+)*");
		Pattern NOTCOMMENT = Pattern.compile("^[\\d+]");
		Pattern BEFORECOM  = Pattern.compile("^(.*)\\!");
//		Pattern COMMENT    = Pattern.compile("(^\\\\*|[a-zA-Z]*)");
		Pattern COMMENT    = Pattern.compile("(^\\*|^[a-zA-Z]+)");
		Matcher match;
		
		// First line
		this.name = input.readLine();
		System.out.println("GscFriskInputSource: "+this.name);
		
		// Second line
		strarr = input.readLine().split("\\s+");
		match = INTNUM.matcher(strarr[0]);
		if (match.find()) this.geomNum = Integer.valueOf(match.group(0)).intValue();
		// Arrays 
		this.geomDepth = new double[this.geomNum][alt.getNumberDepths()];
		
		System.out.printf("   Reading source %s with %d geometries\n",this.name,this.geomNum);
		
		// Arrays initialization
		geomName 	= new String[this.geomNum];
		geomWei 	= new double[this.geomNum];
		geomTyp 	= new String[this.geomNum];
		numPnt 		= new int[this.geomNum];
		mMin 		= new double[this.geomNum];
		mfdDist 	= new int[this.geomNum];
		geomDepth 	= new double[this.geomNum][alt.getNumberDepths()];
		geomWei 	= new double[this.geomNum];
		rupLenPar 	= new double[this.geomNum][3];	
		nu 			= new double[this.geomNum][alt.getNumberNuBeta()];
		beta 		= new double[this.geomNum][alt.getNumberNuBeta()];
		mMax 		= new double[this.geomNum][alt.getNumberMaxMag()];
		geomDip1 	= new double[this.geomNum][alt.getNumberDepths()];
		geomDip2 	= new double[this.geomNum][alt.getNumberDepths()];
		geomZ1 		= new double[this.geomNum][alt.getNumberDepths()];
		geomZ2 		= new double[this.geomNum][alt.getNumberDepths()];
		geomZ3 		= new double[this.geomNum][alt.getNumberDepths()];

		// Reads geometry blocks 
		for (i=0; i<this.geomNum; i++ ) {
			// First line of Geometry i
			this.geomName[i] = input.readLine();
			// Second line of Geometry i 
			strarr = input.readLine().split("\\s+");
			match = INTNUM.matcher(strarr[0]);
			if (match.find()) this.geomWei[i] = Integer.valueOf(match.group(0)).intValue();
			
			// Third line of Geometry i
			line = input.readLine(); line = line.trim();
			this.geomTyp[i] = line;
			System.out.printf("   Type: %s\n",this.geomTyp[i]);
			
			// Reading 
			if (this.geomTyp[i].equals("area")){	
				
				// Reading comments
				if (skipComm){
					for (int ww=0; ww < 3; ww++){
						line = input.readLine(); line = line.trim();
					}
				}
				
				// Fourth line of Geometry i 
				line = input.readLine(); 
				line = removeInfo(line);
				String[] aa = line.split("\\s+");
				for (int w=0; w<aa.length; w++){
					this.geomDepth[i][w] = Double.valueOf(aa[w]).doubleValue();
				}
				
			} else if (this.geomTyp[i].equals("fault")) {
				for (j=0; j<alt.getNumberDepths(); j++) {
					line = input.readLine();
					strarr = line.split("\\s+");
					// 
					match = FLOATNUM.matcher(strarr[0]);
					if (match.find()) this.geomDip1[i][j] = Double.valueOf(match.group(0)).doubleValue();
					match = FLOATNUM.matcher(strarr[1]);
					if (match.find()) this.geomDip2[i][j] = Double.valueOf(match.group(0)).doubleValue();
					match = FLOATNUM.matcher(strarr[2]);
					if (match.find()) this.geomZ1[i][j]   = Double.valueOf(match.group(0)).doubleValue();
					match = FLOATNUM.matcher(strarr[3]);
					if (match.find()) this.geomZ2[i][j]   = Double.valueOf(match.group(0)).doubleValue();
					match = FLOATNUM.matcher(strarr[4]);
					if (match.find()) this.geomZ3[i][j]   = Double.valueOf(match.group(0)).doubleValue();
				} 
				// Rupture-length relation
				line = input.readLine();
				strarr = line.split("\\s+");
				match = FLOATNUM.matcher(strarr[0]);
				if (match.find()) this.rupLenPar[i][0] = Double.valueOf(match.group(0)).doubleValue();
				match = FLOATNUM.matcher(strarr[1]);
				if (match.find()) this.rupLenPar[i][1] = Double.valueOf(match.group(0)).doubleValue();
				match = FLOATNUM.matcher(strarr[2]);
				if (match.find()) this.rupLenPar[i][2] = Double.valueOf(match.group(0)).doubleValue();
			}
			
			// Sixth line
			line = input.readLine(); line = line.trim();
			strarr = line.split("\\s+");
			match = INTNUM.matcher(strarr[0]);
			if (match.find()) this.numPnt[i] = Integer.valueOf(match.group(0)).intValue();
			System.out.printf("   Number of vertexes %d\n",this.numPnt[i]);
			LocationList locl = new LocationList();
			
			// Coords block
			for (j=0; j<this.numPnt[i]; j++) {
				line = input.readLine(); line = line.trim();
				strarr = line.split("\\s+");
				
				// Longitude
				match = FLOATNUM.matcher(strarr[0]);
				if (match.find()) lon = Double.valueOf(match.group(0)).doubleValue();
				
				// Latitude
				match = FLOATNUM.matcher(strarr[1]); 
				if (match.find()) lat = Double.valueOf(match.group(0)).doubleValue();
				
//				System.out.println(strarr[0]+" :"+lon+" | "+lat);
				locl.add(new Location(lat,lon));
			}	
			this.coords.add(locl);
			
			// Magnitude data
			line = input.readLine();
			strarr = line.split("\\s+");
			match = FLOATNUM.matcher(strarr[0]);
			if (match.find())  this.mMin[i] = Double.valueOf(match.group(0)).doubleValue();
			for (j=0; j<alt.getNumberMaxMag(); j++) {
				//System.out.printf("%d %d \n",strarr.length,j);
				match = FLOATNUM.matcher(strarr[j+1]);
				if (match.find()) this.mMax[i][j] = Double.valueOf(match.group(0)).doubleValue();	
			}		
			// FMD type
			line = input.readLine();
			strarr = line.split("\\s+");
			match = INTNUM.matcher(strarr[0]);
			if (match.find()) this.mfdDist[i] = Integer.valueOf(match.group(0)).intValue();
			// FMD data
			line = input.readLine();
			strarr = line.split("\\s+");
			
			for (j=0; j<alt.getNumberNuBeta(); j++) {
			
				match = FLOATNUM.matcher(strarr[j*2]);
				if (match.find()) this.nu[i][j] = Double.valueOf(match.group(0)).doubleValue();
				
				match = FLOATNUM.matcher(strarr[j*2+1]);
				if (match.find()) this.beta[i][j] = Double.valueOf(match.group(0)).doubleValue();
				
				System.out.printf("nu: %8.3f beta: %6.3f\n",this.nu[i][j],this.beta[i][j]);
			}	
			
		}
	}
	
	/**
	 * This removes the commented part of a string
	 * @param str
	 * @return
	 */
	private String removeInfo(String str){
		String tmpstr = str.trim();
		String[] aa = str.split("\\!");
		return aa[0];
	}
}
