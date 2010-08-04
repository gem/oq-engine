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

package org.opensha.sha.earthquake.rupForecastImpl.GEM;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.calc.magScalingRelations.MagScalingRelationship;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Somerville_2006_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagAreaRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;

import scratch.ned.slab.SlabSurfaceGenerator;


/**
 * <p>Title: TestSubductionZoneERF</p>
 * <p>Description: T  </p>
 *
 * @author Ned Field
 * Date : Oct 27 , 2009
 * @version 1.0
 */

public class TestSubductionZoneERF extends EqkRupForecast{

  //for Debug purposes
  private static String  C = new String("FloatingPoissonFaultERF");
  private boolean D = false;

  //name for this classs
  public final static String  NAME = "GEM Test Subduction Zone ERF";

  // this is the source (only 1 for this ERF)
  private ArrayList<FloatingPoissonFaultSource> sources;

  /*
  // rupture offset parameter stuff
  public final static String OFFSET_PARAM_NAME =  "Rupture Offset";
  private final static String OFFSET_PARAM_INFO =  "The amount floating ruptures are offset along the fault";
  private final static String OFFSET_PARAM_UNITS = "km";
  private final static double OFFSET_PARAM_MIN = .01;
  private final static double OFFSET_PARAM_MAX = 100;
  private Double OFFSET_PARAM_DEFAULT = new Double(1);
  */

  // rupture offset parameter stuffs
  public final static String SLAB_GRID_SPACING_PARAM_NAME =  "Slab Grid Spacing";
  private final static String SLAB_GRID_SPACING_PARAM_INFO =  "Ave discretization of the subduction-zone slab";
  private final static String SLAB_GRID_SPACING_PARAM_UNITS = "km";
  private final static int SLAB_GRID_SPACING_PARAM_MIN = 10;
  private final static int SLAB_GRID_SPACING_PARAM_MAX = 100;
  private Integer SLAB_GRID_SPACING_PARAM_DEFAULT = new Integer(25);

  // parameter declarations
  DoubleParameter rupOffsetParam;
  IntegerParameter slabGridSpacingParam;
  
  ArrayList<String> clipFileNames = new ArrayList<String>();
  ArrayList<String> grdFileNames = new ArrayList<String>();
  ArrayList<String> sourceNames = new ArrayList<String>();


  /**
   * Constructor for this source (no arguments)
   */
  public TestSubductionZoneERF() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);
/*
    // create the rupOffset spacing param
    rupOffsetParam = new DoubleParameter(OFFSET_PARAM_NAME,OFFSET_PARAM_MIN,
        OFFSET_PARAM_MAX,OFFSET_PARAM_UNITS,OFFSET_PARAM_DEFAULT);
    rupOffsetParam.setInfo(OFFSET_PARAM_INFO);
 */   
    // create the rupOffset spacing param
    slabGridSpacingParam = new IntegerParameter( SLAB_GRID_SPACING_PARAM_NAME, 
    		SLAB_GRID_SPACING_PARAM_MIN, SLAB_GRID_SPACING_PARAM_MAX, 
    		SLAB_GRID_SPACING_PARAM_UNITS, SLAB_GRID_SPACING_PARAM_DEFAULT );
    slabGridSpacingParam.setInfo(SLAB_GRID_SPACING_PARAM_INFO);


    // add the adjustable parameters to the list
//    adjustableParams.addParameter(rupOffsetParam);
    adjustableParams.addParameter(slabGridSpacingParam);

    // register the parameters that need to be listened to
//    rupOffsetParam.addParameterChangeListener(this);
    slabGridSpacingParam.addParameterChangeListener(this);
    
    clipFileNames.add("scratch/ned/slab/slab1_usgs_data/sam_slab1.0.clip.txt");
    clipFileNames.add("scratch/ned/slab/slab1_usgs_data/sum_slab1.0.clip.txt");
    clipFileNames.add("scratch/ned/slab/slab1_usgs_data/kur_slab1.0.clip.txt");
    
    grdFileNames.add("scratch/ned/slab/slab1_usgs_data/sam_slab1.0_clip.grd");
    grdFileNames.add("scratch/ned/slab/slab1_usgs_data/sum_slab1.0_clip.grd");
    grdFileNames.add("scratch/ned/slab/slab1_usgs_data/kur_slab1.0_clip.grd");
 
    sourceNames.add("South American Subduction Zone");
    sourceNames.add("Sumatra Subduction Zone");
    sourceNames.add("Kuril Subduction Zone");

  }



   /**
    * update the source based on the paramters (only if a parameter value has changed)
    */
   public void updateForecast(){
     String S = C + "updateForecast::";

     if(parameterChangeFlag) {

       MagScalingRelationship magScalingRel = new Somerville_2006_MagAreaRel();
       double aveGridSpaceing = slabGridSpacingParam.getValue().doubleValue();
       double sigma=0;
       double aspectRatio=1;
       double rake=90;
       double minMag=7.9;
       
       SlabSurfaceGenerator surfGen = new SlabSurfaceGenerator();
       
       sources = new ArrayList<FloatingPoissonFaultSource>();
       
       for(int s=0; s<clipFileNames.size(); s++) {
    	   ApproxEvenlyGriddedSurface surf = surfGen.getGriddedSurface(clipFileNames.get(s), 
    			   grdFileNames.get(s), aveGridSpaceing);
    	   System.out.println("SurfaceLength="+surf.getSurfaceLength()+"\tSurfaceWidth="+surf.getSurfaceWidth()+
    			   "\taveGridSpacing="+surf.getGridSpacingAlongStrike()+"\tnumRows="+surf.getNumRows()+"\tnumCols="+surf.getNumCols());

    	   double totArea = surf.getSurfaceLength()*surf.getSurfaceWidth();
    	   double magMax = magScalingRel.getMedianMag(totArea);
    	   double floatArea = (0.5*surf.getSurfaceWidth())*(0.5*surf.getSurfaceWidth());
    	   double magFloat = magScalingRel.getMedianMag(floatArea);
    	   System.out.println("totArea="+totArea+"\tmagMax="+magMax+"\tfloatArea="+floatArea+"\tmagFloat="+magFloat);
   	   
    	   magMax = ((double)Math.round(10*magMax))/10.0;
    	   magFloat = ((double)Math.round(10*magFloat))/10.0;
    	   
    	   System.out.println("rounded magMax="+magMax+"\trounded magFloat="+magFloat);
    	   
    	   ArbIncrementalMagFreqDist magDist = new ArbIncrementalMagFreqDist(magFloat, magMax, 2);
    	   magDist.set(0, 0.01);
    	   magDist.set(1, 0.001);
    	   
    	   double rupOffset = 0.25*surf.getSurfaceWidth();
//    	   double rupOffset = ((Double) rupOffsetParam.getValue()).doubleValue();
    	   
    	   FloatingPoissonFaultSource src = new FloatingPoissonFaultSource(magDist,
                   surf, (MagScalingRelationship) magScalingRel,
                   sigma, aspectRatio,
                   rupOffset,
                   rake, timeSpan.getDuration(), minMag);
    	   
    	   src.setName(sourceNames.get(s));
    	   sources.add(src);
    	   
//   		System.out.println("numRuptures="+src.getNumRuptures());

    	   
       }
       parameterChangeFlag = false;
     }

   }




   /**
    * Return the earhthquake source at index i.   Note that this returns a
    * pointer to the source held internally, so that if any parameters
    * are changed, and this method is called again, the source obtained
    * by any previous call to this method will no longer be valid.
    *
    * @param iSource : index of the desired source (only "0" allowed here).
    *
    * @return Returns the ProbEqkSource at index i
    *
    */
   public ProbEqkSource getSource(int iSource) {

    return sources.get(iSource);
   }


   /**
    * Returns the number of earthquake sources (always "1" here)
    *
    * @return integer value specifying the number of earthquake sources
    */
   public int getNumSources(){
     return sources.size();
   }


    /**
     *  This returns a list of sources (contains only one here)
     *
     * @return ArrayList of Prob Earthquake sources
     */
    public ArrayList  getSourceList(){
       return sources;
    }


  /**
   * Return the name for this class
   *
   * @return : return the name for this class
   */
   public String getName(){
     return NAME;
   }
   
	public static void main(String[] args) {
		TestSubductionZoneERF testERF = new TestSubductionZoneERF();
		testERF.updateForecast();
		for(int s=0;s<testERF.getNumSources();s++) {
			ProbEqkSource src = testERF.getSource(s);
			System.out.println("src "+s+"\t numRups="+src.getNumRuptures());
			for(int r=0; r<src.getNumRuptures();r++) {
				EvenlyGriddedSurfaceAPI surf = src.getRupture(r).getRuptureSurface();
				Iterator it = surf.getLocationsIterator();
				int num=0;
				while(it.hasNext()) {
					num +=1;
					it.next();
				}
				System.out.println("\trup "+r+"\t mag="+src.getRupture(r).getMag()+"\t numRows="+surf.getNumRows()+"\t numCos="+
						surf.getNumCols()+"\t numLocsFromIterator="+num+"\t numLocsFromList="+surf.getLocationList().size()+
						"\t rupArea="+surf.getSurfaceArea());
			}
		}
	}

}
