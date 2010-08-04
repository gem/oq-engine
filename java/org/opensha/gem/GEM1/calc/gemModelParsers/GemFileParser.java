package org.opensha.gem.GEM1.calc.gemModelParsers;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.hamcrest.core.IsInstanceOf;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMGridSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

public class GemFileParser {
	
	protected ArrayList<GEMSourceData> srcDataList;
	private static boolean INFO = false; 
	
	/**
	 * This gives the list of GEMSourceData parsed from the input ascii file
	 * @return srcDataList 
	 */
	public ArrayList<GEMSourceData> getList (){
		return this.srcDataList;
	}
	
	/**
	 * This returns the list of GEMAreaSourceData obects contained in the parsed list
	 * @return 
	 */
	public ArrayList<GEMSourceData> getAreaSourceList (){
		ArrayList<GEMSourceData> areaList = new ArrayList<GEMSourceData>();
		for (GEMSourceData src: this.srcDataList){
			if (src instanceof GEMAreaSourceData) areaList.add(src);
		}
		if (areaList.size() < 1) areaList = null;
		return areaList;
	}
	
	/**
	 * This returns the list of GEMAreaSourceData objects contained in the parsed list
	 * @return 
	 */
	public ArrayList<GEMSourceData> getFaultSourceList (){
		ArrayList<GEMSourceData> faultList = new ArrayList<GEMSourceData>();
		for (GEMSourceData src: this.srcDataList){
			if (src instanceof GEMFaultSourceData) faultList.add(src);
		}
		if (faultList.size() < 1) faultList = null;
		return faultList;
	}
	
	/**
	 * This returns the list of GEMSubductionFaultSourceData objects contained in the parsed list
	 * @return 
	 */
	public ArrayList<GEMSourceData> getSubductionFaultSourceList (){
		ArrayList<GEMSourceData> faultList = new ArrayList<GEMSourceData>();
		for (GEMSourceData src: this.srcDataList){
			if (src instanceof GEMSubductionFaultSourceData) faultList.add(src);
		}
		if (faultList.size() < 1) faultList = null;
		return faultList;
	}
	
	/**
	 * This returns the list of GEMPointSourceData objects contained in the parsed list
	 * @return 
	 */
	public ArrayList<GEMSourceData> getPointSourceList (){
		ArrayList<GEMSourceData> pointSource = new ArrayList<GEMSourceData>();
		for (GEMSourceData src: this.srcDataList){
			if (src instanceof GEMPointSourceData) pointSource.add(src);
		}
		if (pointSource.size() < 1) pointSource = null;
		return pointSource;
	}
	
	/**
	 * This is just for testing purposed and will be removed
	 */
	public void setList (ArrayList<GEMSourceData> lst){
		this.srcDataList = lst;
	}
	
	/**
	 * 
	 * @return number of source data objects 
	 */
	public int getNumSources(){
		return this.srcDataList.size();
	}
	
	/**
	 * This writes to a file the coordinates of the polygon. The format of the outfile is compatible 
	 * with the GMT psxy multiple segment file. The separator adopted here is the default separator 
	 * suggested in GMT (i.e. '>') 
	 *   
	 * @param file
	 * @throws IOException 
	 */
	public void writeAreaGMTfile (FileWriter file) throws IOException{
		BufferedWriter out = new BufferedWriter(file);
		
		// Search for area sources
		int idx = 0;
		for (GEMSourceData dat: srcDataList){
			if (dat instanceof GEMAreaSourceData){

				// Get the polygon vertexes
				GEMAreaSourceData src = (GEMAreaSourceData) dat;
				
				// Get polygon area 
				double area = src.getArea();
				
				// Total scalar seismic moment above m 
				double totMom = 0.0;
				double momRate = 0.0;
				double magThreshold = 5.0;

				for (IncrementalMagFreqDist mfdffm: src.getMagfreqDistFocMech().getMagFreqDistList()){
					EvenlyDiscretizedFunc momRateDist = mfdffm.getMomentRateDist();
				
					if (INFO) System.out.println("MinX "+momRateDist.getMinX()+" MaxX"+momRateDist.getMaxX());
					if (INFO) System.out.println("Mo(idx5):"+src.getMagfreqDistFocMech().getMagFreqDist(0).getMomentRate(5));
					
					for (int i=0; i < momRateDist.getNum(); i++ ){
						if (momRateDist.get(i).getX() >= magThreshold){
							totMom += momRateDist.get(i).getY();
							if (INFO) System.out.println(i+" "+momRateDist.get(i).getY());
						}
					}
					
				}
				momRate = totMom / area;
				
				// Info
				if (INFO) System.out.println(src.getID()+" "+totMom);
				
				// Write separator +
				// Scalar seismic moment rate per units of time and area above 'magThreshold'
				out.write(String.format("> -Z %6.2e idx %d \n",Math.log10(momRate),idx));
				
				// Write trace coordinates
				for (Location loc: src.getRegion().getBorder()){
					out.write(String.format("%+7.3f %+6.3f %+6.2f\n",
							loc.getLongitude(),
							loc.getLatitude(),
							loc.getDepth()));
					System.out.printf("%+7.3f %+6.3f %+6.2f\n",
							loc.getLongitude(),
							loc.getLatitude(),
							loc.getDepth());
				}
			}	
		}
		// Write separator
		out.write('>');
		out.close();
	}
	
	/**
	 * This writes area source polygons into KML file
	 */
	public void writeAreaKMLfile (FileWriter file) throws IOException{
		
		// output KML file
		BufferedWriter out = new BufferedWriter(file);
		
		// XML header
		out.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
		// KML namespace declaration
		out.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n");
		
		out.write("<Document>\n");
		
	    out.write("<Style id=\"transRedPoly\">");
	    out.write("<LineStyle>");
	    out.write("<width>1.5</width>");
	    out.write("</LineStyle>");
	    out.write("<PolyStyle>");
	    out.write("<color>7d0000ff</color>");
	    out.write("</PolyStyle>");
	    out.write("</Style>");
		
		// loop over area sources
		for (GEMSourceData dat: srcDataList){
			
			if (dat instanceof GEMAreaSourceData){
				
				// create area source object
				GEMAreaSourceData src = (GEMAreaSourceData) dat;
				
				// create Placemarck object
				out.write("<Placemark>\n");
				
				// define name
				out.write("<name>"+src.getName()+"</name>\n");
				
				out.write("<styleUrl>#transRedPoly</styleUrl>");
				
				// description
				String descr = "";
				// loop  over focal mechanisms
				for(int ifm=0;ifm<src.getMagfreqDistFocMech().getNumFocalMechs();ifm++){
					
					descr = descr + "Mmin = "+src.getMagfreqDistFocMech().getMagFreqDist(ifm).getMinX()+", "+
					                "Mmax = "+src.getMagfreqDistFocMech().getMagFreqDist(ifm).getMaxX()+", "+
					                "TotalCumulativeRate (ev/yr) = "+src.getMagfreqDistFocMech().getMagFreqDist(ifm).getTotalIncrRate()+", "+
					                "Strike: "+src.getMagfreqDistFocMech().getFocalMech(ifm).getStrike()+", "+
					                "Dip: "+src.getMagfreqDistFocMech().getFocalMech(ifm).getDip()+", "+
					                "Rake: "+src.getMagfreqDistFocMech().getFocalMech(ifm).getRake()+", "+
					                "Average Hypo Depth (km): "+src.getAveHypoDepth();
					
				}
				out.write("<description>\n");
				out.write(descr+"\n");
				out.write("</description>\n");
				
				// write outer polygon
				out.write("<Polygon>\n");
				// outer boundary
				out.write("<outerBoundaryIs>\n");
				out.write("<LinearRing>\n");
				out.write("<coordinates>\n");
				// loop over coordinates
				for(int ic=0;ic<src.getRegion().getBorder().size();ic++){
					double lon = src.getRegion().getBorder().get(ic).getLongitude();
					double lat = src.getRegion().getBorder().get(ic).getLatitude();
					out.write(lon+","+lat+"\n");
				}
				out.write("</coordinates>\n");
				out.write("</LinearRing>\n");
				out.write("</outerBoundaryIs>\n");
				
			    // write inner polygons
				// loop over interiors
				if(src.getRegion().getInteriors()!=null){
					for(int ireg=0;ireg<src.getRegion().getInteriors().size();ireg++){
						out.write("<innerBoundaryIs>\n");
						out.write("<LinearRing>\n");
						out.write("<coordinates>\n");
						// loop over coordinates
						for(int ic=0;ic<src.getRegion().getInteriors().get(ireg).size();ic++){
							double lon = src.getRegion().getInteriors().get(ireg).get(ic).getLongitude();
							double lat = src.getRegion().getInteriors().get(ireg).get(ic).getLatitude();
							out.write(lon+","+lat+"\n");
						}
						out.write("</coordinates>\n");
						out.write("</LinearRing>\n");
						out.write("</innerBoundaryIs>\n");
					}
				}

				out.write("</Polygon>\n");
				out.write("</Placemark>\n");

			}
			
			
			
		}
		out.write("</Document>\n");
		out.write("</kml>");
		out.close();
	}
	
	/**
	 * This writes the coordinates of the fault traces to a file. The format of the outfile is 
	 * compatible with the GMT psxy multiple segment file format. The separator adopted here is the 
	 * default separator suggested in GMT (i.e. '>') 
	 *   
	 * @param file
	 * @throws IOException 
	 */
	public void writeFaultGMTfile (FileWriter file) throws IOException{
		BufferedWriter out = new BufferedWriter(file);
		
		// Search for fault sources
		for (GEMSourceData dat: srcDataList){
			if (dat instanceof GEMFaultSourceData){
				// Write the trace coordinate to a file
				GEMFaultSourceData src = (GEMFaultSourceData) dat;
				// Trace length
				Double len = src.getTrace().getTraceLength();
				// Total scalar seismic moment above m 
				EvenlyDiscretizedFunc momRateDist = src.getMfd().getMomentRateDist();
				double totMom = 0.0;
				double momRate = 0.0;
				double magThreshold = 5.0;
				for (int i=0; i < momRateDist.getNum(); i++ ){
					if (momRateDist.get(i).getX() >= magThreshold){
						totMom += totMom;
					}
				}
				momRate = totMom / len;
				// Write separator
				out.write(String.format("> -Z %6.2e",Math.log10(momRate)));
				// Write trace coordinates
				for (Location loc: src.getTrace()){
					out.write(String.format("%+7.3f %+6.3f %+6.2f",
							loc.getLongitude(),
							loc.getLatitude(),
							loc.getDepth()));
				}

			}	

		}
		out.write('>');
	}
	
}
