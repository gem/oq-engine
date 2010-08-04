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

package org.opensha.sha.calc.IM_EventSet.v01;


import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.imr.PropagationEffect;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.depricated.BA_2006_AttenRel;
import org.opensha.sha.imr.attenRelImpl.depricated.CB_2006_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.util.SiteTranslator;



/**
 * <p>Title: PagerShakeMapCalc</p>
 *
 * <p>Description: </p>
 *
 * @author Nitin Gupta, Vipin Gupta, and Ned Field
 * @version 1.0
 */
public class IM_EventSetScenarioForCEA implements ParameterChangeWarningListener{


	private EqkRupture eqkRupture;
	private ArrayList attenRelList;
	private ArrayList vs30List ;
	private ArrayList distanceJBList;
	private ArrayList rupDistList;
	private ArrayList stationIds;
	private LocationList locList;
	private ArrayList imtSupported;
	private final static String EVENT_SET_FILE_CEA = "org/opensha/sha/calc/IM_EventSetCalc_v01/eventSetFileCEA.txt";
	private final static String CB2006_TEST_FILE = "CB_2006_TestFile.txt";
	private final static String BA2006_TEST_FILE = "BA_2006_TestFile.txt";
	private final static String CY2006_TEST_FILE = "CY_2006_TestFile.txt";
	  // site translator
	private SiteTranslator siteTranslator = new SiteTranslator();
	
	private double minLat = Double.MAX_VALUE;
	private double maxLat = Double.MIN_VALUE;
	private double minLon = Double.MAX_VALUE;
	private double maxLon = Double.NEGATIVE_INFINITY;
	SimpleFaultParameter faultParameter;
	
	public void  createSimpleFaultParam(SimpleFaultParameter faultParameter){
		
		ArrayList lats = new ArrayList();
		lats.add(new Double(33.875));
		lats.add(new Double( (33.933+ 33.966)/2));
		lats.add(new Double(34.039));
		
		ArrayList lons = new ArrayList();
		lons.add(new Double(-117.873));
		lons.add(new Double((-118.124-118.135)/2));
		lons.add(new Double(-118.334));
		
		double dip = 27.5;
		ArrayList dips = new ArrayList();
		dips.add(new Double(dip));
		
		double dow = 27.00;
		double lowDepth = dow*Math.sin(dip);
		
		ArrayList depths = new ArrayList();
		depths.add(new Double(0.0));
		depths.add(new Double(lowDepth));
		faultParameter.initLatLonParamList();
		faultParameter.initDipParamList();
		faultParameter.initDepthParamList();
		
		faultParameter.setAll(SimpleFaultParameter.DEFAULT_GRID_SPACING, 
				lats, lons, dips, depths, SimpleFaultParameter.FRANKEL);
		faultParameter.setEvenlyGriddedSurfaceFromParams();
	}
	
	private void createRuptureSurface(){
	
	    eqkRupture = new EqkRupture();
	    faultParameter = new SimpleFaultParameter("Set Fault Surface");
		createSimpleFaultParam(faultParameter);
		eqkRupture.setRuptureSurface((EvenlyGriddedSurfaceAPI)faultParameter.getValue());
		eqkRupture.setAveRake(90);
		eqkRupture.setMag(7.15);
	}
	
	
	private void readSiteFile(){
		ArrayList fileLines = null;
		vs30List = new ArrayList();
		stationIds = new ArrayList();
		rupDistList = new ArrayList();
		distanceJBList =  new ArrayList();
		locList = new LocationList();
		try {
			fileLines = FileUtils.loadFile(EVENT_SET_FILE_CEA);
			for(int i=1;i<fileLines.size();++i){
				String line = (String)fileLines.get(i);
				StringTokenizer st = new StringTokenizer(line);
				st.nextToken();
				stationIds.add(st.nextToken().trim());
				st.nextToken();
				st.nextToken();
				distanceJBList.add(Double.parseDouble(st.nextToken().trim()));
				rupDistList.add(Double.parseDouble(st.nextToken().trim()));
				vs30List.add(Integer.parseInt(st.nextToken().trim()));
				double lon = Double.parseDouble(st.nextToken().trim());
				double lat = Double.parseDouble(st.nextToken().trim());
				if(lat < this.minLat)
					minLat = lat;
				if(lat > this.maxLat)
					maxLat = lat;
				if(lon < this.minLon)
					minLon = lon;
				if(lon > this.maxLon)
					maxLon = lon;
					
				locList.add(new Location(lat,lon));
			}
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}		
	}
	
	
	private void createAttenRelInstances(){
		attenRelList = new ArrayList();
		attenRelList.add(createIMRClassInstance("BA_2006_AttenRel"));
		attenRelList.add(createIMRClassInstance("CB_2006_AttenRel"));
		attenRelList.add(createIMRClassInstance("CY_2006_AttenRel"));
	}
	
	

	  /**
	  * Creates a class instance from a string of the full class name including packages.
	  * This is how you dynamically make objects at runtime if you don't know which\
	  * class beforehand. For example, if you wanted to create a BJF_1997_AttenRel you can do
	  * it the normal way:<P>
	  *
	  * <code>BJF_1997_AttenRel imr = new BJF_1997_AttenRel()</code><p>
	  *
	  * If your not sure the user wants this one or AS_1997_AttenRel you can use this function
	  * instead to create the same class by:<P>
	  *
	  * <code>BJF_1997_AttenRel imr =
	  * (BJF_1997_AttenRel)ClassUtils.createNoArgConstructorClassInstance("org.opensha.sha.imt.attenRelImpl.BJF_1997_AttenRel");
	  * </code><p>
	  *
	  */

	  private ScalarIntensityMeasureRelationshipAPI createIMRClassInstance(String AttenRelClassName){
	    String attenRelClassPackage = "org.opensha.sha.imr.attenRelImpl.";
	      try {
	        Class listenerClass = Class.forName( "org.opensha.commons.param.event.ParameterChangeWarningListener" );
	        Object[] paramObjects = new Object[]{ this };
	        Class[] params = new Class[]{ listenerClass };
	        Class imrClass = Class.forName(attenRelClassPackage+AttenRelClassName);
	        Constructor con = imrClass.getConstructor( params );
	        ScalarIntensityMeasureRelationshipAPI attenRel = (ScalarIntensityMeasureRelationshipAPI)con.newInstance( paramObjects );
	        //setting the Attenuation with the default parameters
	        attenRel.setParamDefaults();
	        return attenRel;
	      } catch ( ClassCastException e ) {
	        e.printStackTrace();
	      } catch ( ClassNotFoundException e ) {
	       e.printStackTrace();
	      } catch ( NoSuchMethodException e ) {
	       e.printStackTrace();
	      } catch ( InvocationTargetException e ) {
	        e.printStackTrace();
	      } catch ( IllegalAccessException e ) {
	        e.printStackTrace();
	      } catch ( InstantiationException e ) {
	        e.printStackTrace();
	      }
	      return null;
	  }
	
	  
	  private void createIMTList(){
		  imtSupported = new ArrayList();
		  imtSupported.add(PGA_Param.NAME);
		  imtSupported.add(SA_Param.NAME+" "+"0.3");
		  imtSupported.add(SA_Param.NAME+" "+"1.0");
	  }

	  
	  /**
	   * set the site params in IMR according to basin Depth and vs 30
	   * @param imr
	   * @param lon
	   * @param lat
	   * @param willsClass
	   * @param basinDepth
	   */
	  private void setSiteParamsInIMR(ScalarIntensityMeasureRelationshipAPI imr,
	                                  int vs30) {

	    Iterator it = imr.getSiteParamsIterator(); // get site params for this IMR
	    while (it.hasNext()) {
	      ParameterAPI tempParam = (ParameterAPI) it.next();
	      //adding the site Params from the CVM, if site is out the range of CVM then it
	      //sets the site with whatever site Parameter Value user has choosen in the application
	      SiteDataValue<Double> val = new SiteDataValue<Double>(SiteDataAPI.TYPE_VS30,
	    		  SiteDataAPI.TYPE_FLAG_INFERRED, new Double(vs30));
	      boolean flag = siteTranslator.setParameterValue(tempParam, val);

	      if (!flag) {
	        String message = "cannot set the site parameter \"" + tempParam.getName() +
	            "\" from Vs30 = \"" + vs30 + "\"" +
	            "\n (no known, sanctioned translation - please set by hand)";
	      }
	    }
	  }
	  
	  
	  private void createMeanStdDevFile(){
		  PropagationEffect propEffect = new PropagationEffect();
		  propEffect.setEqkRupture(eqkRupture);
		  
		  try {
			FileWriter fw = new FileWriter("IM_MeanStdDevFile.txt");
			FileWriter fwTest;

			fw.write("AttenID,IMT,SiteID,Mean,Stdev\n");
			
			for(int i=0;i<this.attenRelList.size();++i){
				boolean writenTofile = false;
				ScalarIntensityMeasureRelationshipAPI attenRel = (ScalarIntensityMeasureRelationshipAPI)attenRelList.get(i);
				if(attenRel.getName().equals(BA_2006_AttenRel.NAME))
					fwTest = new FileWriter(this.BA2006_TEST_FILE);
				else if(attenRel.getName().equals(CB_2006_AttenRel.NAME))
					fwTest = new FileWriter(this.CB2006_TEST_FILE);
				else
					fwTest = new FileWriter(this.CY2006_TEST_FILE);
				Site site = new Site();
				Iterator it = attenRel.getSiteParamsIterator(); // get site params for this IMR
			    while (it.hasNext()) {
			      ParameterAPI tempParam = (ParameterAPI) it.next();
			      site.addParameter(tempParam);
			    }
				for(int j=0;j<imtSupported.size();++j){
					String imt = (String)imtSupported.get(j);
					double period = -1;
					if(imt.startsWith(SA_Param.NAME)){
						StringTokenizer st = new StringTokenizer(imt);
						String  saName = st.nextToken().trim();
						period = Double.parseDouble(st.nextToken().trim());
						attenRel.setIntensityMeasure(saName);
						attenRel.getParameter(PeriodParam.NAME).setValue(new Double(period));
					}
					
					if(period ==-1)
						attenRel.setIntensityMeasure(imt);
						
					for(int k=0;k<this.locList.size();++k){
						Location loc = locList.get(k);
						site.setLocation(loc);
						setSiteParamsInIMR(attenRel,((Integer)vs30List.get(k)).intValue());
						propEffect.setSite(site);
						attenRel.setPropagationEffect(propEffect);
						double mean = Math.exp(attenRel.getMean());
						double stdDev = attenRel.getStdDev();
						fw.write(attenRel.getName()+","+imt+","+(String)this.stationIds.get(k)+
								","+mean+","+stdDev+"\n");
						if(!writenTofile){
							fwTest.write("Selected Site : " +attenRel.getSite().getLocation().toString()+"\n");
							fwTest.write("--------------\n");
							fwTest.write(attenRel.getName()+" Params:\n"+attenRel.getAllParamMetadata().replaceAll(";","\n")+"\n");
							fwTest.write("--------------\n");
						}
					}
					writenTofile = true;
					fwTest.close();
				}
			}
			fw.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		  
	  }

	  
	  
   public static void main(String args[]){
	   IM_EventSetScenarioForCEA imEventSetScenario = new IM_EventSetScenarioForCEA();
	   imEventSetScenario.createAttenRelInstances();
	   imEventSetScenario.createIMTList();
	   imEventSetScenario.createRuptureSurface();
	   imEventSetScenario.readSiteFile();
	   imEventSetScenario.createMeanStdDevFile();
   }
  /**
   *  Function that must be implemented by all Listeners for
   *  ParameterChangeWarnEvents.
   *
   * @param  event  The Event which triggered this function call
   */
  public void parameterChangeWarning(ParameterChangeWarningEvent e) {

    String S = " : parameterChangeWarning(): ";

    WarningParameterAPI param = e.getWarningParameter();

    //System.out.println(b);
    param.setValueIgnoreWarning(e.getNewValue());

  }


}
