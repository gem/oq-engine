package org.opensha.sha.simulators.eqsim_v04;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.NamedObjectComparator;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.PlaneUtils;
import org.opensha.commons.util.FileUtils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.EvenlyGridCenteredSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

/**
 * This class reads and writes various files, as well as doing some analysis of simulator results.
 * 
 * Note that this class could extend the "Container" defined in EQSIM, but it's not clear that generality is necessary.
 * 
 * Things to keep in mind:
 * 
 * Indexing in the EQSIM files starts from 1, not zero.  Therefore, the index for the ith RectangularElement 
 * in rectElementsList (rectElementsList.getIndex()) is one less than i (same goes for vertexList).
 * 
 * All units in EQSIM files are SI
 * 
 * Note that slip rates in EQSIM files are in units of m/s, whereas we convert these to m/yr internally here.
 * 
 * We assume the first vertex in each element here is the first on the upper edge 
 * (traceFlag=2 if the element is at the top); this is not checked for explicitly
 * 
 * @author field
 *
 */
public class General_EQSIM_Tools {

	protected final static boolean D = false;  // for debugging
	
	private ArrayList<FaultSectionPrefData> allFaultSectionPrefData;
	ArrayList<RectangularElement> rectElementsList;
	ArrayList<Vertex> vertexList;
	ArrayList<ArrayList<RectangularElement>> rectElementsListForSections;
	ArrayList<ArrayList<Vertex>> vertexListForSections;
	ArrayList<String> namesOfSections;
	ArrayList<Integer> faultIDs_ForSections;
	
	final static String GEOM_FILE_SIG = "EQSim_Input_Geometry_2";	// signature of the geometry file
	final static int GEOM_FILE_SPEC_LEVEL = 2;
	final static double SECONDS_PER_YEAR = 365*24*60*60;


	/**
	 * This constructor makes the list of RectangularElements from a UCERF2 deformation model
	 * @param deformationModelID	- D2.1 = 82; D2.2 = 83; D2.3 = 84; D2.4 = 85; D2.5 = 86; D2.6 = 87
	 * @param aseisReducesArea		- whether or not to reduce area (otherwise reduces slip rate?)
	 * @param maxDiscretization		- the maximum element size
	 */
	public General_EQSIM_Tools(int deformationModelID, boolean aseisReducesArea,
			double maxDiscretization) {
		
		mkElementsFromUCERF2_DefMod(deformationModelID, aseisReducesArea, maxDiscretization);
	}
	
	
	/**
	 * This constructor loads the data from an EQSIM_v04 Geometry file
	 * @param filePathName		 - full path and file name
	 */
	public General_EQSIM_Tools(String filePathName) {
		
		ArrayList<String> lines=null;
		try {
			lines = FileUtils.loadJarFile(filePathName);
			System.out.println("Number of file lines: "+lines.size()+" (in "+filePathName+")");
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
		loadFromEQSIMv04_Lines(lines);
	}
	
	
	/**
	 * This constructor loads the data from an EQSIM_v04 Geometry file
	 * @param url		 - full URL path name
	 */
	public General_EQSIM_Tools(URL url) {
		
		ArrayList<String> lines=null;
		
		try {
			lines = FileUtils.loadFile(url);
			System.out.println("Number of file lines: "+lines.size()+" (in "+url+")");
		} catch (Exception e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		loadFromEQSIMv04_Lines(lines);
	}

	
	
	
	
	/**
	 * This creates the data from lines from an EQSIM Geometry file
	 * @param lines
	 * @return
	 */
	private void loadFromEQSIMv04_Lines(ArrayList<String> lines) {
		
		rectElementsList = new ArrayList<RectangularElement>();
		vertexList = new ArrayList<Vertex>();
		rectElementsListForSections = new ArrayList<ArrayList<RectangularElement>> ();
		vertexListForSections = new ArrayList<ArrayList<Vertex>>();
		namesOfSections = new ArrayList<String>();
		faultIDs_ForSections = new ArrayList<Integer>();
		
//		Iterator<String> linesIterator = lines.iterator();
		ListIterator<String> linesIterator = lines.listIterator();
		
		// get & check first line (must be the signature line)
		String line = linesIterator.next();
		StringTokenizer tok = new StringTokenizer(line);
		int kindOfLine = Integer.parseInt(tok.nextToken());
		String fileSignature = tok.nextToken();
		int fileSpecLevel = Integer.parseInt(tok.nextToken());
		if(kindOfLine != 101 || !fileSignature.equals(GEOM_FILE_SIG) || fileSpecLevel < GEOM_FILE_SPEC_LEVEL)
			throw new RuntimeException("wrong type of input file");
		
		int n_sction=-1, n_vertex=-1, n_triangle=-1, n_rectangle=-1;

		while (linesIterator.hasNext()) {
			
			line = linesIterator.next();
			tok = new StringTokenizer(line);
			kindOfLine = Integer.parseInt(tok.nextToken());
			
			// read "Fault System Summary Record" (values kept are use as a check later)
			if(kindOfLine == 200) {
				n_sction=Integer.parseInt(tok.nextToken());
				n_vertex=Integer.parseInt(tok.nextToken());
				n_triangle=Integer.parseInt(tok.nextToken());
				n_rectangle=Integer.parseInt(tok.nextToken());
				// the rest of the line contains:
				// lat_lo lat_hi lon_lo lon_hi depth_lo depth_hi comment_text
			}
			
			// read "Fault Section Information Record"
			if(kindOfLine == 201) {
				int sid = Integer.parseInt(tok.nextToken());
				String name = tok.nextToken();
				int n_sect_vertex=Integer.parseInt(tok.nextToken());
				int n_sect_triangle=Integer.parseInt(tok.nextToken());
				int n_sect_rectangle=Integer.parseInt(tok.nextToken());
				tok.nextToken(); // lat_lo
				tok.nextToken(); // lat_hi
				tok.nextToken(); // lon_lo
				tok.nextToken(); // lon_hi
				tok.nextToken(); // depth_lo
				tok.nextToken(); // depth_hi
				tok.nextToken(); // das_lo
				tok.nextToken(); // das_hi
				int fault_id = Integer.parseInt(tok.nextToken());
				// the rest of the line contains: comment_text
				
				// check for triangular elements
				if(n_sect_triangle>0) throw new RuntimeException("Don't yet support trinagles");
				
				namesOfSections.add(name);
				faultIDs_ForSections.add(fault_id);

				// read the vertices for this section
				ArrayList<Vertex> verticesForThisSect = new ArrayList<Vertex>();
				for(int v=0; v<n_sect_vertex; v++) {
					line = linesIterator.next();
					tok = new StringTokenizer(line);
					kindOfLine = Integer.parseInt(tok.nextToken());
					if(kindOfLine != 202) throw new RuntimeException("Problem with file (line should start with 202)");
					int index = Integer.parseInt(tok.nextToken());
					double lat = Double.parseDouble(tok.nextToken());
					double lon = Double.parseDouble(tok.nextToken());
					double depth = -Double.parseDouble(tok.nextToken())/1000; 	// convert to km
					double das = Double.parseDouble(tok.nextToken())/1000;		// convert to km
					int trace_flag = Integer.parseInt(tok.nextToken());
					// the rest of the line contains:
					// comment_text
					
					Vertex vertex = new Vertex(lat,lon,depth, index, das, trace_flag); 
					verticesForThisSect.add(vertex);
					vertexList.add(vertex);
				}
				vertexListForSections.add(verticesForThisSect);
				
				// now read the elements
				ArrayList<RectangularElement> rectElemForThisSect = new ArrayList<RectangularElement>();
				for(int r=0; r<n_sect_rectangle; r++) {
					line = linesIterator.next();
					tok = new StringTokenizer(line);
					kindOfLine = Integer.parseInt(tok.nextToken());
					if(kindOfLine != 204) throw new RuntimeException("Problem with file (line should start with 204)");
					int index = Integer.parseInt(tok.nextToken());
					int vertex_1 = Integer.parseInt(tok.nextToken());
					int vertex_2 = Integer.parseInt(tok.nextToken());
					int vertex_3 = Integer.parseInt(tok.nextToken());
					int vertex_4 = Integer.parseInt(tok.nextToken());
				    double rake = Double.parseDouble(tok.nextToken());
				    double slip_rate = Double.parseDouble(tok.nextToken())*SECONDS_PER_YEAR; // convert to meters per year
				    double aseis_factor = Double.parseDouble(tok.nextToken());
				    double strike = Double.parseDouble(tok.nextToken());
				    double dip = Double.parseDouble(tok.nextToken());
				    int perfect_flag = Integer.parseInt(tok.nextToken());
					// the rest of the line contains:
					// comment_text
				    boolean perfectBoolean = false;
				    if(perfect_flag == 1) perfectBoolean = true;
				    Vertex[] vertices = new Vertex[4];
				    
				    vertices[0] = vertexList.get(vertex_1-1);
				    vertices[1] = vertexList.get(vertex_2-1);
				    vertices[2] = vertexList.get(vertex_3-1);
				    vertices[3] = vertexList.get(vertex_4-1);
				    int numAlongStrike = -1;// unknown
				    int numDownDip = -1;	// unknown
				    FocalMechanism focalMechanism = new FocalMechanism(strike,dip,rake);
				    RectangularElement rectElem = new RectangularElement(index, vertices, name, fault_id, sid, numAlongStrike, 
				    													numDownDip, slip_rate, aseis_factor, focalMechanism, perfectBoolean);
				    rectElemForThisSect.add(rectElem);
				    rectElementsList.add(rectElem);
				    
				}
				rectElementsListForSections.add(rectElemForThisSect);
			}
		}
		
		// check the numbers of things:  n_sction, n_vertex, n_triangle, n_rectangle
		if(n_sction != namesOfSections.size())
			throw new RuntimeException("something wrong with number of sections");
		if(n_vertex != vertexList.size())
			throw new RuntimeException("something wrong with number of vertices");
		if(n_rectangle != rectElementsList.size())
			throw new RuntimeException("something wrong with number of eleents");
		
		System.out.println("namesOfSections.size()="+namesOfSections.size()+"\tvertexList.size()="+vertexList.size()+"\trectElementsList.size()="+rectElementsList.size());
		
		// check that indices are in order:
		for(int i=0;i<vertexList.size();i++) {
			if(i != vertexList.get(i).getIndex()-1) throw new RuntimeException("vertexList index problem at "+i);
		}
		for(int i=0;i<rectElementsList.size();i++) {
			if(i != rectElementsList.get(i).getIndex()-1) throw new RuntimeException("rectElementsList index problem at "+i);
		}
		
	}

	
	
	/**
	 * This returns the list of RectangularElement objects
	 * @return
	 */
	public ArrayList<RectangularElement> getElementsList() { return rectElementsList; }

	
	/**
	 * This makes the elements from a UCERF2 deformation model
	 * @param deformationModelID	- D2.1 = 82; D2.2 = 83; D2.3 = 84; D2.4 = 85; D2.5 = 86; D2.6 = 87
	 * @param aseisReducesArea		- whether or not to reduce area (otherwise reduces slip rate?)
	 * @param maxDiscretization		- the maximum element size
	 */
	public void mkElementsFromUCERF2_DefMod(int deformationModelID, boolean aseisReducesArea, 
			double maxDiscretization) {
		
		rectElementsList = new ArrayList<RectangularElement>();
		vertexList = new ArrayList<Vertex>();
		rectElementsListForSections = new ArrayList<ArrayList<RectangularElement>> ();
		vertexListForSections = new ArrayList<ArrayList<Vertex>>();
		namesOfSections = new ArrayList<String>();
		faultIDs_ForSections = null;	// no info for this

		
		// fetch the sections
		DeformationModelPrefDataFinal deformationModelPrefDB = new DeformationModelPrefDataFinal();
		allFaultSectionPrefData = deformationModelPrefDB.getAllFaultSectionPrefData(deformationModelID);

		//Alphabetize:
		Collections.sort(allFaultSectionPrefData, new NamedObjectComparator());

		/*		  
		  // write sections IDs and names
		  for(int i=0; i< this.allFaultSectionPrefData.size();i++)
				System.out.println(allFaultSectionPrefData.get(i).getSectionId()+"\t"+allFaultSectionPrefData.get(i).getName());
		 */

		// remove those with no slip rate
		if (D)System.out.println("Removing the following due to NaN slip rate:");
		for(int i=allFaultSectionPrefData.size()-1; i>=0;i--)
			if(Double.isNaN(allFaultSectionPrefData.get(i).getAveLongTermSlipRate())) {
				if(D) System.out.println("\t"+allFaultSectionPrefData.get(i).getSectionName());
				allFaultSectionPrefData.remove(i);
			}	 
				
		// Loop over sections and create the simulator elements
		int elementID =0;
		int numberAlongStrike = 0;
		int numberDownDip;
		int faultNumber = -1; // unknown for now
		int sectionNumber =0;
		double elementSlipRate=0;
		double elementAseis;
		double elementStrike=0, elementDip=0, elementRake=0;
		String sectionName;
//		System.out.println("allFaultSectionPrefData.size() = "+allFaultSectionPrefData.size());
		for(int i=0;i<allFaultSectionPrefData.size();i++) {
			ArrayList<RectangularElement> sectionElementsList = new ArrayList<RectangularElement>();
			ArrayList<Vertex> sectionVertexList = new ArrayList<Vertex>();
			sectionNumber +=1; // starts from 1, not zero
			FaultSectionPrefData faultSectionPrefData = allFaultSectionPrefData.get(i);
			StirlingGriddedSurface surface = new StirlingGriddedSurface(faultSectionPrefData.getSimpleFaultData(aseisReducesArea), maxDiscretization, maxDiscretization);
			EvenlyGridCenteredSurface gridCenteredSurf = new EvenlyGridCenteredSurface(surface);
			double elementLength = gridCenteredSurf.getGridSpacingAlongStrike();
			double elementDDW = gridCenteredSurf.getGridSpacingDownDip(); // down dip width
			elementRake = faultSectionPrefData.getAveRake();
			elementSlipRate = faultSectionPrefData.getAveLongTermSlipRate()/1000;
			elementAseis = faultSectionPrefData.getAseismicSlipFactor();
			sectionName = faultSectionPrefData.getName();
			for(int col=0; col<gridCenteredSurf.getNumCols();col++) {
				numberAlongStrike += 1;
				for(int row=0; row<gridCenteredSurf.getNumRows();row++) {
					elementID +=1; // starts from 1, not zero
					numberDownDip = row+1;
					Location centerLoc = gridCenteredSurf.get(row, col);
					Location top1 = surface.get(row, col);
					Location top2 = surface.get(row, col+1);
					Location bot1 = surface.get(row+1, col);
					double[] strikeAndDip = PlaneUtils.getStrikeAndDip(top1, top2, bot1);
					elementStrike = strikeAndDip[0];
					elementDip = strikeAndDip[1];	
					
					double hDistAlong = elementLength/2;
					double dipRad = Math.PI*elementDip/180;
					double vDist = (elementDDW/2)*Math.sin(dipRad);
					double hDist = (elementDDW/2)*Math.cos(dipRad);
					
//					System.out.println(elementID+"\telementDDW="+elementDDW+"\telementDip="+elementDip+"\tdipRad="+dipRad+"\tvDist="+vDist+"\thDist="+hDist);
					
					LocationVector vect = new LocationVector(elementStrike+180, hDistAlong, 0);
					Location newMid1 = LocationUtils.location(centerLoc, vect);  // half way down the first edge
					vect.set(elementStrike-90, hDist, -vDist); // up-dip direction
					Location newTop1 = LocationUtils.location(newMid1, vect);
					vect.set(elementStrike+90, hDist, vDist); // down-dip direction
					Location newBot1 = LocationUtils.location(newMid1, vect);
					 
					vect.set(elementStrike, hDistAlong, 0);
					Location newMid2 = LocationUtils.location(centerLoc, vect); // half way down the other edge
					vect.set(elementStrike-90, hDist, -vDist); // up-dip direction
					Location newTop2 = LocationUtils.location(newMid2, vect);
					vect.set(elementStrike+90, hDist, vDist); // down-dip direction
					Location newBot2 = LocationUtils.location(newMid2, vect);
					
					 // @param traceFlag - tells whether is on the fault trace  (0 means no; 1 means yes, but not
					 // 		              the first or last point; 2 means yes & it's the first; and 3 means yes 
					 //                    & it's the last point)
					
					
					// set DAS
					double das1 = col*elementLength;	// this is in km
					double das2 = das1+elementLength;	// this is in km
					// set traceFlag - tells whether is on the fault trace  (0 means no; 1 means yes, but not the first or last point; 2 means yes & it's the first; and 3 means yes & it's the last point)
					int traceFlagBot = 0;
					int traceFlagTop1 = 0;
					int traceFlagTop2 = 0;
					if(row ==0) {
						traceFlagTop1 = 1;
						traceFlagTop2 = 1;
					}
					if(row==0 && col==0) traceFlagTop1 = 2;
					if(row==0 && col==gridCenteredSurf.getNumCols()-1) traceFlagTop2 = 3;

					Vertex[] elementVertices = new Vertex[4];
					elementVertices[0] = new Vertex(newTop1,vertexList.size()+1, das1, traceFlagTop1);  
					elementVertices[1] = new Vertex(newBot1,vertexList.size()+2, das1, traceFlagBot);
					elementVertices[2] = new Vertex(newBot2,vertexList.size()+3, das2, traceFlagBot);
					elementVertices[3] = new Vertex(newTop2,vertexList.size()+4, das2, traceFlagTop2);
					
					FocalMechanism focalMech = new FocalMechanism(elementStrike, elementDip, elementRake);
										
					RectangularElement simSurface =
						new RectangularElement(elementID, elementVertices, sectionName,
								faultNumber, sectionNumber, numberAlongStrike, numberDownDip,
								elementSlipRate, elementAseis, focalMech, true);
					
					rectElementsList.add(simSurface);
					vertexList.add(elementVertices[0]);
					vertexList.add(elementVertices[1]);
					vertexList.add(elementVertices[2]);
					vertexList.add(elementVertices[3]);
					
					sectionElementsList.add(simSurface);
					sectionVertexList.add(elementVertices[0]);
					sectionVertexList.add(elementVertices[1]);
					sectionVertexList.add(elementVertices[2]);
					sectionVertexList.add(elementVertices[3]);

					
//					String line = elementID + "\t"+
//						numberAlongStrike + "\t"+
//						numberDownDip + "\t"+
//						faultNumber + "\t"+
//						sectionNumber + "\t"+
//						(float)elementSlipRate + "\t"+
//						(float)elementStrength + "\t"+
//						(float)elementStrike + "\t"+
//						(float)elementDip + "\t"+
//						(float)elementRake + "\t"+
//						(float)newTop1.getLatitude() + "\t"+
//						(float)newTop1.getLongitude() + "\t"+
//						(float)newTop1.getDepth()*-1000 + "\t"+
//						(float)newBot1.getLatitude() + "\t"+
//						(float)newBot1.getLongitude() + "\t"+
//						(float)newBot1.getDepth()*-1000 + "\t"+
//						(float)newBot2.getLatitude() + "\t"+
//						(float)newBot2.getLongitude() + "\t"+
//						(float)newBot2.getDepth()*-1000 + "\t"+
//						(float)newTop2.getLatitude() + "\t"+
//						(float)newTop2.getLongitude() + "\t"+
//						(float)newTop2.getDepth()*-1000 + "\t"+
//						sectionName;
//
//					System.out.println(line);
				}
			}
			rectElementsListForSections.add(sectionElementsList);
			vertexListForSections.add(sectionVertexList);
			namesOfSections.add(faultSectionPrefData.getName());
		}
		System.out.println("rectElementsList.size()="+rectElementsList.size());
		System.out.println("vertexList.size()="+vertexList.size());
		
		/*
		for(int i=0;i<allFaultSectionPrefData.size();i++) {
			ArrayList<RectangularElement> elList = rectElementsListForSections.get(i);
			ArrayList<Vertex> verList = vertexListForSections.get(i);;
			System.out.println(allFaultSectionPrefData.get(i).getName());
			System.out.println("\tEl Indices:  "+elList.get(0).getIndex()+"\t"+elList.get(elList.size()-1).getIndex());
//			System.out.println("\tVer Indices:  "+verList.get(0).getIndex()+"\t"+verList.get(verList.size()-1).getIndex());
		}
		*/
	}
	
	
	/**
	 * this returns a list of elements created from the given lines from a Ward-format file
	 * @param lines
	 * @return
	 */
	public static ArrayList<RectangularElement> getElementsFromWardFileLines(ArrayList<String> lines) {
		ArrayList<RectangularElement> elements = new ArrayList<RectangularElement>();
		
		for (String line : lines) {
			if (line == null || line.length() == 0)
				continue;
			elements.add(new RectangularElement(line,0));
		}
		return elements;
	}
	
	
	public void writeToWardFile(String fileName) throws IOException {
		FileWriter efw = new FileWriter(fileName);
		for (RectangularElement surface : rectElementsList) {
			efw.write(surface.toWardFormatLine() + "\n");
		}
		efw.close();
	}
	
	
	/**
	 * The creates a EQSIM V04 Geometry file for the given instance.
	 * @param fileName
	 * @param infoLines - each line here should NOT end with a new line char "\n" (this will be added)
	 * @param titleLine
	 * @param author
	 * @param date
	 * @throws IOException
	 */
	public void writeTo_EQSIM_V04_GeometryFile(String fileName, ArrayList<String> infoLines, String titleLine, 
			String author, String date) throws IOException {
			FileWriter efw = new FileWriter(fileName);
			
			// write the standard file signature info
			efw.write("101 "+GEOM_FILE_SIG +" "+GEOM_FILE_SPEC_LEVEL+ "\n");
			
			// add the file-specific meta data records/lines
			if(titleLine!=null)
				efw.write("111 "+titleLine+ "\n");
			if(author!=null)
				efw.write("112 "+author+ "\n");
			if(date!=null)
				efw.write("113 "+date+ "\n");
			if(infoLines!=null)
				for(int i=0; i<infoLines.size();i++)
					efw.write("110 "+infoLines.get(i)+ "\n");
			
			// add the standard descriptor records/lines for the Geometry file (read from another file)
			String fullPath = "org/opensha/sha/simulators/eqsim_v04/ALLCAL_Model_v04/ALLCAL_Ward_Geometry.dat";
			ArrayList<String> lines=null;
			try {
				lines = FileUtils.loadJarFile(fullPath);
			} catch (FileNotFoundException e) {
				e.printStackTrace();
			} catch (IOException e) {
				e.printStackTrace();
			}
			for(int l=0;l<lines.size();l++) {
				String line = lines.get(l);
				StringTokenizer tok = new StringTokenizer(line);
				int kindOfLine = Integer.parseInt(tok.nextToken());
				if(kindOfLine==120 || kindOfLine==121 || kindOfLine==103)
					efw.write(line+"\n");
			}
			
			// now add the data records/lines 
			
			// Fault System Summary Record:
			// 200 n_section n_vertex n_triangle n_rectangle lat_lo lat_hi lon_lo lon_hi depth_lo depth_hi comment_text
			efw.write("200 "+namesOfSections.size()+" "+vertexList.size()+" 0 "+rectElementsList.size()+" "+
							getMinMaxFileString(vertexList, false)+"\n");

			// loop over sections
			for(int i=0;i<namesOfSections.size();i++) {
				ArrayList<Vertex> vertListForSect = vertexListForSections.get(i);
				ArrayList<RectangularElement> rectElemForSect = rectElementsListForSections.get(i);
				String fault_id;
				if(faultIDs_ForSections == null)
					fault_id = "NA";
				else
					fault_id = faultIDs_ForSections.get(i).toString();
				// Fault Section Information Record:
				// 201 sid name n_vertex n_triangle n_rectangle lat_lo lat_hi lon_lo lon_hi depth_lo depth_hi das_lo das_hi fault_id comment_text
				efw.write("201 "+(i+1)+" "+namesOfSections.get(i)+" "+vertListForSect.size()+" 0 "+
						rectElemForSect.size()+" "+getMinMaxFileString(vertListForSect, true)+" "+fault_id+"\n");
				for(int v=0; v<vertListForSect.size(); v++) {
					Vertex vert = vertListForSect.get(v);
					// Vertex Record: 202 index lat lon depth das trace_flag comment_text
					efw.write("202 "+vert.getIndex()+" "+(float)vert.getLatitude()+" "+(float)vert.getLongitude()+" "+
							(float)(vert.getDepth()*-1000)+" "+(float)vert.getDAS()*1000+" "+vert.getTraceFlag()+"\n");
				}
				for(int e=0; e<rectElemForSect.size(); e++) {
					RectangularElement elem = rectElemForSect.get(e);
					Vertex[] vert = elem.getVertices();
					FocalMechanism focalMech = elem.getFocalMechanism();
					// Rectangle Record:  204 index vertex_1 vertex_2 vertex_3 vertex_4 rake slip_rate aseis_factor strike dip perfect_flag comment_text
					efw.write("204 "+elem.getIndex()+" "+vert[0].getIndex()+" "+vert[1].getIndex()+" "+vert[2].getIndex()+" "+
							vert[3].getIndex()+" "+(float)focalMech.getRake()+" "+(float)(elem.getSlipRate()/SECONDS_PER_YEAR)+" "+
							(float)elem.getAseisFactor()+" "+(float)focalMech.getStrike()+" "+(float)focalMech.getDip()
							+" "+elem.getPerfectInt()+"\n");
				}
			}
			
			// add the last line
			efw.write("999 End\n");

			efw.close();
	}
	
	
	/**
	 * This produces the string of min and max lat, lon, depth, and (optionally) DAS from the
	 * given list of vertices.  There are no spaces before or after the first and last values,
	 * respectively.  Depth and DAS values are converted to meters (from km).
	 * @param vertexList
	 * @param includeDAS
	 * @return
	 */
	private String getMinMaxFileString(ArrayList<Vertex> vertexList, boolean includeDAS) {
		double minLat=Double.MAX_VALUE, maxLat=-Double.MAX_VALUE;
		double minLon=Double.MAX_VALUE, maxLon=-Double.MAX_VALUE;
		double minDep=Double.MAX_VALUE, maxDep=-Double.MAX_VALUE;
		double minDAS=Double.MAX_VALUE, maxDAS=-Double.MAX_VALUE;
		for(Vertex vertex: vertexList) {
			if(vertex.getLatitude()<minLat) minLat = vertex.getLatitude();
			if(vertex.getLongitude()<minLon) minLon = vertex.getLongitude();
			if(vertex.getDepth()<minDep) minDep = vertex.getDepth();
			if(vertex.getDAS()<minDAS) minDAS = vertex.getDAS();
			if(vertex.getLatitude()>maxLat) maxLat = vertex.getLatitude();
			if(vertex.getLongitude()>maxLon) maxLon = vertex.getLongitude();
//			if(!includeDAS) System.out.println(maxLon);
			if(vertex.getDepth()>maxDep) maxDep = vertex.getDepth();
			if(vertex.getDAS()>maxDAS) maxDAS = vertex.getDAS();
		}
		String string = (float)minLat+" "+(float)maxLat+" "+(float)minLon+" "+(float)maxLon+" "+(float)maxDep*-1000+" "+(float)minDep*-1000;
		if(includeDAS) string += " "+(float)minDAS*1000+" "+(float)maxDAS*1000;
		return string;
	}

	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		
		long startTime=System.currentTimeMillis();
		System.out.println("Starting");
		
		General_EQSIM_Tools test = new General_EQSIM_Tools(82, false, 4.0);
//		test.getElementsList();
		String writePath = "testEQSIM_Output.txt";
		try {
			test.writeTo_EQSIM_V04_GeometryFile(writePath, null, "test UCERF2 output", 
					"Ned Field", "Aug 3, 2010");
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		/*
		// THE FOLLOWING TEST LOOKS GOOD FROM A VISUAL INSPECTION
//		String fullPath = "org/opensha/sha/simulators/eqsim_v04/ExamplesFromKeith/NCA_Ward_Geometry.dat.txt";
		String fullPath = "org/opensha/sha/simulators/eqsim_v04/ALLCAL_Model_v04/ALLCAL_Ward_Geometry.dat";
		General_EQSIM_Tools test = new General_EQSIM_Tools(fullPath);
		
		String writePath = "testEQSIM_Output.txt";
		try {
			test.writeTo_EQSIM_V04_GeometryFile(writePath, null, "test output", 
					"Ned Field", "Aug 3, 2010");
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		*/
		
		
		int runtime = (int)(System.currentTimeMillis()-startTime)/1000;
		System.out.println("This Run took "+runtime+" seconds");
	}
}
