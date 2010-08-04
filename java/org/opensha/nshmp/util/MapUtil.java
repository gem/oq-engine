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

package org.opensha.nshmp.util;

import java.util.ArrayList;

/**
 * <p>Title: MapUtil</p>
 *
 * <p>Description: This class allows the user to get the listing of the NSHMP map
 * files.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public final class MapUtil {


  //Lists to hold the Map info and link to Map files
  public static ArrayList mapInfo;
  public static ArrayList mapFiles;

  //link to the directory where all the map files are located
  public static final String mapURL_Path =
	"http://earthquake.usgs.gov/research/hazmaps/pdfs/";


  /**
   * This will create list of maps that user can view, based on Region and
   * data-edition selected by the user.
   * @param selectedRegion String
   * @param selectedDataEdition String
   */
  public static void createMapList(String selectedRegion,
                                         String selectedDataEdition) {

    mapInfo = new ArrayList();
    mapFiles = new ArrayList();
    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES) &&
        selectedDataEdition.equals(GlobalConstants.data_1996)) {
      //adding the Map Info to be shown to the user
      mapInfo.add("MAP 131A(1996 Conterminous US) - Peak Horizontal Acceleration with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131B(1996 Conterminous US) - Peak Horizontal Acceleration with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131C(1996 Conterminous US) - Peak Horizontal Acceleration with 2% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131D(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 0.2sec period(5% Damping) " +
                  "with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131E(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 0.2sec period(5% Damping) " +
                  "with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131F(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 0.2sec period(5% Damping) " +
                  "with 2% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131G(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 0.3sec period(5% Damping) " +
                  "with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131H(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 0.3sec period(5% Damping) " +
                  "with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131I(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 0.3sec period(5% Damping) " +
                  "with 2% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131J(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 1.0sec period(5% Damping) " +
                  "with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131K(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 1.0sec period(5% Damping) " +
                  "with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 131L(1996 Conterminous US) - Horizontal Spectral Response Acceleration for 1.0sec period(5% Damping) " +
                  "with 2% Prob. of Exceedance in 50 years.");

      mapInfo.add("MAP 130A  (Calif.,Nevada, Western US) - Peak Horizontal Acceleration with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130B (Calif.,Nevada, Western US)- Peak Horizontal Acceleration with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130C (Calif.,Nevada, Western US)- Peak Horizontal Acceleration with 2% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130D (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 0.2sec period(5% Damping) " +
                  "with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130E (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 0.2sec period(5% Damping) " +
                  "with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130F (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 0.2sec period(5% Damping) " +
                  "with 2% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130G (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 0.3sec period(5% Damping) " +
                  "with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130H (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 0.3sec period(5% Damping) " +
                  "with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130I (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 0.3sec period(5% Damping) " +
                  "with 2% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130J (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 1.0sec period(5% Damping) " +
                  "with 10% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130K (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 1.0sec period(5% Damping) " +
                  "with 5% Prob. of Exceedance in 50 years.");
      mapInfo.add("MAP 130L (Calif.,Nevada, Western US)- Horizontal Spectral Response Acceleration for 1.0sec period(5% Damping) " +
                  "with 2% Prob. of Exceedance in 50 years.");
      //adding the actual map files name with their path
      mapFiles.add(mapURL_Path+"USGS-1996-Map131A-US-pga-10-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131B-US-pga-05-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131C-US-pga-02-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131D-US-0_2sec-10-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131E-US-0_2sec-05-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131F-US-0_2sec-02-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131G-US-0_3sec-10-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131H-US-0_3sec-05-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131I-US-0_3sec-02-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131J-US-1_0sec-10-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131K-US-1_0sec-05-050.pdf");
      mapFiles.add(mapURL_Path+"USGS-1996-Map131L-US-1_0sec-02-050.pdf");

      mapFiles.add(mapURL_Path + "USGS-1996-Map130A-WUS-pga-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130B-WUS-pga-05-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130C-WUS-pga-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130D-WUS-0_2sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130E-WUS-0_2sec-05-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130F-WUS-0_2sec-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130G-WUS-0_3sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130H-WUS-0_3sec-05-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130I-WUS-0_3sec-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130J-WUS-1_0sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130K-WUS-1_0sec-05-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1996-Map130L-WUS-1_0sec-02-050.pdf");
    }
    else if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES) &&
             selectedDataEdition.equals(GlobalConstants.data_2002)) {
      mapInfo.add("MAP I-2883, SHEET 1 - Peak Horizontal Acceleration"+
                  " with 10% Probability of Exceedance in 50 Years.");
      mapInfo.add("MAP I-2883, SHEET 2 - Peak Horizontal Acceleration"+
                  " with 2% Probability of Exceedance in 50 Years.");
      mapInfo.add("MAP I-2883, SHEET 3 - Horizontal Spectral Response Acceleration for " +
                  "0.2 Second Period (5% Damping) with 10% Probability of Exceedance in 50 Years");
      mapInfo.add("MAP I-2883, SHEET 4 - Horizontal Spectral Response Acceleration for " +
                  "0.2 Second Period (5% Damping) with 2% Probability of Exceedance in 50 Years");
      mapInfo.add("MAP I-2883, SHEET 5 - Horizontal Spectral Response Acceleration for " +
                  "1.0 Second Period (5% Damping) with 10% Probability of Exceedance in 50 Years");
      mapInfo.add("MAP I-2883, SHEET 6 - Horizontal Spectral Response Acceleration for " +
                  "1.0 Second Period (5% Damping) with 2% Probability of Exceedance in 50 Years");
      mapFiles.add(mapURL_Path +"USGS-2002-Map2883I-sh1-US-pga-10-050.pdf");
      mapFiles.add(mapURL_Path +"USGS-2002-Map2883I-sh2-US-pga-02-050.pdf");
      mapFiles.add(mapURL_Path +"USGS-2002-Map2883I-sh3-US-0_2sec-10-050.pdf");
      mapFiles.add(mapURL_Path +"USGS-2002-Map2883I-sh4-US-0_2sec-02-050.pdf");
      mapFiles.add(mapURL_Path +"USGS-2002-Map2883I-sh5-US-1_0sec-10-050.pdf");
      mapFiles.add(mapURL_Path +"USGS-2002-Map2883I-sh6-US-1_0sec-02-050.pdf");
    }
    else if (selectedRegion.equals(GlobalConstants.ALASKA) &&
        selectedDataEdition.equals(GlobalConstants.data_1998)){
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration with 10% Probability of Exceedance in 50 years");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration for 0.2sec period (5% Damping) with 10% Prob. "+
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration for 0.3sec period (5% Damping) with 10% Prob. "+
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration for 1.0sec period (5% Damping) with 10% Prob. "+
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration with 2% Probability of Exceedance in 50 years");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration for 0.2sec period (5% Damping) with 2% Prob. "+
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration for 0.3sec period (5% Damping) with 2% Prob. "+
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2679, Sheet1 - Peak Horizontal Acceleration for 1.0sec period (5% Damping) with 2% Prob. "+
                  "of Exceedance in 50 years.");

      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh1-AK-pga-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh1-AK-0_2sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh1-AK-0_3sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh1-AK-1_0sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh2-AK-pga-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh2-AK-0_2sec-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh2-AK-0_3sec-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2679I-sh2-AK-1_0sec-02-050.pdf");

    }
    else if(selectedRegion.equals(GlobalConstants.HAWAII) &&
            selectedDataEdition.equals(GlobalConstants.data_1998)) {
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration with 10% Probability of Exceedance in 50 years");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration for 0.2sec period (5% Damping) with 10% Prob. " +
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration for 0.3sec period (5% Damping) with 10% Prob. " +
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration for 1.0sec period (5% Damping) with 10% Prob. " +
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration with 2% Probability of Exceedance in 50 years");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration for 0.2sec period (5% Damping) with 2% Prob. " +
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration for 0.3sec period (5% Damping) with 2% Prob. " +
                  "of Exceedance in 50 years.");
      mapInfo.add("Map I-2724, Sheet1 - Peak Horizontal Acceleration for 1.0sec period (5% Damping) with 2% Prob. " +
                  "of Exceedance in 50 years.");


      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh1-HI-pga-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh1-HI-0_2sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh1-HI-0_3sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh1-HI-1_0sec-10-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh2-HI-pga-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh2-HI-0_2sec-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh2-HI-0_3sec-02-050.pdf");
      mapFiles.add(mapURL_Path + "USGS-1998-Map2724I-sh2-HI-1_0sec-02-050.pdf");

    }
    else if(selectedDataEdition.equals(GlobalConstants.ASCE_1998) ||
            selectedDataEdition.equals(GlobalConstants.ASCE_2002)){
      mapInfo.add("Figure 9.4.1.1(a) - MCE Ground Motion for the Conterminous US of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(b) - MCE Ground Motion for the Conterminous US of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(c) - MCE Ground Motion for the Region 1(California/Western Nevada) of 0.2sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(d) - MCE Ground Motion for the Region 1(California/Western Nevada) of 1.0sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(e) - MCE Ground Motion for the Region 2(Salt Lake City/Intermountain Area) of 0.2sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(f) - MCE Ground Motion for the Region 2(Salt Lake City/Intermountain Area) of 1.0sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(g) - MCE Ground Motion for Alaska of 0.2 and 1.0sec period Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(h) - MCE Ground Motion for Hawaii of 0.2 and 1.0sec period Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(i) - MCE Ground Motion for Puerto Rico,Culebra,Vieques, St. Thomas, St. John and St. Croix "+
                  "of 0.2 and 1.0sec period Spectral Response Acceleration");
      mapInfo.add("Figure 9.4.1.1(i) - MCE Ground Motion for Guam and Tutuilla"+
                  "of 0.2 and 1.0sec period Spectral Response Acceleration");

      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1a-US.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1b-US.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1c-REG1.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1d-REG1.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1e-REG2.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1f-REG2.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1g-AK.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1h-HI.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1ij-PRGU.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-1998-2002-Figure-9-4-1-1ij-PRGU.pdf");
    }
    else if(selectedDataEdition.equals(GlobalConstants.ASCE_2005)){
      mapInfo.add("Figure 22-1 MCE Ground Motion for the Conterminous US of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 22-2 MCE Ground Motion for the Conterminous US of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 22-3 MCE Ground Motion for the Region 1(California/Western Nevada) of 0.2sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 22-4 MCE Ground Motion for the Region 1(California/Western Nevada) of 1.0sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 22-5 MCE Ground Motion for the Region 2(Salt Lake City/Intermountain Area) of 0.2sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 22-6 MCE Ground Motion for the Region 2(Salt Lake City/Intermountain Area) of 1.0sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 22-7 MCE Ground Motion for the Region 3(New Madrid Area) of 0.2sec "+
                        "Spectral Response Acceleration");
      mapInfo.add("Figure 22-8 MCE Ground Motion for the Region 3(New Madrid Area) of 1.0sec "+
                  "Spectral Response Acceleration");
      mapInfo.add("Figure 22-9 MCE Ground Motion for the Region 4(Charleston, SC Area) of 0.2sec and 1.0sec "+
                        "Spectral Response Acceleration.");
      mapInfo.add("Figure 22-10 MCE Ground Motion for Hawaii of 0.2sec and 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 22-11 MCE Ground Motion for Alaska of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 22-12 MCE Ground Motion for Alaska of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 22-13 MCE Ground Motion for Puerto Rico, Culebra, Vieques, St. Thomas, St. John, and St. Croix of 0.2sec and 1.0sec " +
								"Spectral Response Acceleration");
      mapInfo.add("Figure 22-14 MCE Ground Motion for Guam and Tutuila of 0.2sec and 1.0sec Spectral Response Acceleration");


      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-01.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-02.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-03.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-04.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-05.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-06.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-07.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-08.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-09.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-10.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-11.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-12.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-13.pdf");
      mapFiles.add(mapURL_Path + "ASCE7-2005-Figure22-14.pdf");
    }
    else if (selectedDataEdition.equals(GlobalConstants.IBC_2000) ||
             selectedDataEdition.equals(GlobalConstants.IBC_2003) ||
             selectedDataEdition.equals(GlobalConstants.IBC_2004)) {
      mapInfo.add("Figures 1615 (1) - MCE Ground Motion for the Conterminous US of "+
          "0.2sec Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (2) - MCE Ground Motion for the Conterminous US of "+
          "1.0sec Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (3) - MCE Ground Motion for Region 1(California/Western Nevada) of "+
          "0.2sec Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (4) - MCE Ground Motion for Region 1(California/Western Nevada) of "+
          "1.0sec Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (5) - MCE Ground Motion for Region 2(Salt Lake City/Intermountain Area) of "+
          "0.2sec Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (6) - MCE Ground Motion for Region 2(Salt Lake City/Intermountain Area) of "+
          "1.0sec Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (7) - MCE Ground Motion for Alaska of 0.2 and 1.0sec period Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (8) - MCE Ground Motion for Hawaii of 0.2 and 1.0sec period Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (9) - MCE Ground Motion for Puerto Rico,Culebra,Vieques, St. Thomas, St. John and St. Croix "+
                  "of 0.2 and 1.0sec period Spectral Response Acceleration");
      mapInfo.add("Figures 1615 (10) - MCE Ground Motion for Guam and Tutuila "+
                  "of 0.2 and 1.0sec period Spectral Response Acceleration");

      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-1us.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-2us.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-3ca.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-4ca.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-5slc.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-6slc.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-7ak.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-8hi.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-9_10prgu.pdf");
      mapFiles.add(mapURL_Path+"IBC-2000-2003-Figure-1615-9_10prgu.pdf");
    } else if(selectedDataEdition.equals(GlobalConstants.IBC_2006)) {
      mapInfo.add("Figure 1613.5(1) - MCE Ground Motion for the Conterminous United States of"+
                  " 0.2 sec Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(2) - MCE Ground Motion for the Conterminous United States of"+
                  "1 .0 sec Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(3) - MCE Ground Motion for Region 1(California/Western Nevada) of"+
                  " 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(4) - MCE Ground Motion for Region 1(California/Western Nevada) of" +
                  "1.0 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(5) - MCE Ground Motion for Region 2(Salt Lake City Area)of"+
                  " 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(6) - MCE Ground Motion for Region 2 (Salt Lake City Area)of" +
                  " 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5( 7) - MCE Ground Motion for Region 3(New Madrid Area) of"+
                  " 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(8) - MCE Ground Motion for Region 3(New Madrid Area) of"+
                  " 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(9) - MCE Ground Motion for Region 4(Charleston, SC Area) of"+
                  " 0.2 and 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(10) - MCE Ground Motion for Hawaii of" +
                  " 0.2 and 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(11) - MCE Ground Motion for Alaska of" +
                  " 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(12) - MCE Ground Motion for Alaska of"+
                  " 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("Figure 1613.5(13) - MCE Ground Motion for Puerto Rico, Culebra, Vieques,St. Thomas, St. John, and St. Croix of"+
                  " 0.2 and 1.0 sec period Spectral Acceleration");
      mapInfo.add("Figure 1613.5(14) - MCE Ground Motion for Guam and Tutuila of"+
                  " 0.2 and 1.0 sec period Spectral Acceleration");

      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(01).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(02).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(03).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(04).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(05).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(06).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(07).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(08).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(09).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(10).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(11).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(12).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(13).pdf");
      mapFiles.add(mapURL_Path+"IBC-2006-Figure1613_5(14).pdf");
    }
    else if(selectedDataEdition.equals(GlobalConstants.IRC_2000) ||
        selectedDataEdition.equals(GlobalConstants.IRC_2003)){
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, 48 Conterminous States");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Alaska");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Hawaii");
      mapFiles.add(mapURL_Path+"IRC-2000-2003-Figure-R301-2-2-48states.pdf");
      mapFiles.add(mapURL_Path+"IRC-2000-2003-Figure-R301-2-2-AK.pdf");
      mapFiles.add(mapURL_Path+"IRC-2000-2003-Figure-R301-2-2-HI.pdf");
    }
    else if(selectedDataEdition.equals(GlobalConstants.IRC_2004)){
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, 48 Conterminous States");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Alaska");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Hawaii");


      mapFiles.add(mapURL_Path+"IRC-2004-Figure-R301-2-2-48states.pdf");
      mapFiles.add(mapURL_Path+"IRC-2004-Figure-R301-2-2-AK.pdf");
      mapFiles.add(mapURL_Path+"IRC-2004-Figure-R301-2-2-HI.pdf");
    }
    else if(selectedDataEdition.equals(GlobalConstants.IRC_2006)){
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, 48 Conterminous States");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Alaska");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Hawaii");
      mapInfo.add("Figure R301.2b - IRC Seismic Design Categories, Puerto Rico and the Virgin Islands");

      mapFiles.add(mapURL_Path+"IRC-2006-Figure-R301-2-2-48states.pdf");
      mapFiles.add(mapURL_Path+"IRC-2006-Figure-R301-2-2-AK.pdf");
      mapFiles.add(mapURL_Path+"IRC-2006-Figure-R301-2-2-HI.pdf");
      mapFiles.add(mapURL_Path+"IRC-2006-Figure-R301-2-2-PRVI.pdf");
    }
    else if(selectedDataEdition.equals(GlobalConstants.NEHRP_1997)||
        selectedDataEdition.equals(GlobalConstants.NEHRP_2000)){
      mapInfo.add("MAP 1- MCE Ground Motion for the US of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 2- MCE Ground Motion for the US of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 3- MCE Ground Motion for CA/NV of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 4- MCE Ground Motion for CA/NV of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 5- MCE Ground Motion for Southern Cal. of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 6- MCE Ground Motion for Southern Cal. of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 7- MCE Ground Motion for SF Bay Area of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 8- MCE Ground Motion for SF Bay Area of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 9- MCE Ground Motion for Pacific Northwest of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 10- MCE Ground Motion for Pacific Northwest of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 11- MCE Ground Motion for Salt Lake City and the Intermountain Area of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 12- MCE Ground Motion for Salt Lake City and the Intermountain Area of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 13- MCE Ground Motion for New Madrid of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 14- MCE Ground Motion for New Madrid of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 15- MCE Ground Motion for Charleston of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 16- MCE Ground Motion for Charleston of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 17- MCE Ground Motion for Alaska of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 18- MCE Ground Motion for Alaska of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 19- MCE Ground Motion for Hawaii of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 20- MCE Ground Motion for Hawaii of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 21- MCE Ground Motion for Puerto Rico,Culebra,Vieques, St. Thomas, St. John and St. Croix  of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 22- MCE Ground Motion for Puerto Rico,Culebra,Vieques, St. Thomas, St. John and St. Croix  of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 23- MCE Ground Motion for Guam and Tutuila  of 0.2 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 24- MCE Ground Motion for Guam and Tutuila  of 1.0 sec period Spectral Response Acceleration");
      mapInfo.add("MAP 25- Prob. Eqk Ground Motion for the US of 0.2sec Spectral Response Acceleration, 10% in 50 years");
      mapInfo.add("MAP 26- Prob. Eqk Ground Motion for the US of 1.0sec Spectral Response Acceleration, 10% in 50 years");
      mapInfo.add("MAP 27- Prob. Eqk Ground Motion for the US of 0.2sec Spectral Response Acceleration, 2% in 50 years");
      mapInfo.add("MAP 28- Prob. Eqk Ground Motion for the US of 1.0sec Spectral Response Acceleration, 2% in 50 years");
      mapInfo.add("MAP 29- Prob. Eqk Ground Motion for the CA/NV of 0.2sec Spectral Response Acceleration, 10% in 50 years");
      mapInfo.add("MAP 30- Prob. Eqk Ground Motion for the CA/NV of 1.0sec Spectral Response Acceleration, 10% in 50 years");
      mapInfo.add("MAP 31- Prob. Eqk Ground Motion for the CA/NV of 0.2sec Spectral Response Acceleration, 2% in 50 years");
      mapInfo.add("MAP 32- Prob. Eqk Ground Motion for the CA/NV of 1.0sec Spectral Response Acceleration, 2% in 50 years");

      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-01-us.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-02-us.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-03-canv.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-04-canv.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-05-sca.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-06-sca.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-07-sfbay.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-08-sfbay.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-09-nw.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-10-nw.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-11-slc.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-12-slc.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-13-nm.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-14-nm.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-15-ch.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-16-ch.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-17-ak.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-18-ak.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-19-hi.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-20-hi.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-21-pr.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-22-pr.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-23-gu.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-24-gu.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-25-us.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-26-us.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-27-us.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-28-us.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-29-canv.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-30-canv.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-31-canv.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-1997-2000-Map-32-canv.pdf");
    }
    else if(selectedDataEdition.equals(GlobalConstants.NEHRP_2003)){
      mapInfo.add("Figure 3.3-1 - MCE Ground Motion for the Conterminous US of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-2 - MCE Ground Motion for the Conterminous US of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-3 - MCE Ground Motion for Region 1(California/Western Nevada) of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-4 - MCE Ground Motion for Region 1(California/Western Nevada) of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-5 - MCE Ground Motion for Region 2(Salt Lake City Area) of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-6 - MCE Ground Motion for Region 2(Salt Lake City Area) of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-7 - MCE Ground Motion for Region 3(New Madrid Area) of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-8 - MCE Ground Motion for Region 3(New Madrid Area) of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-9 - MCE Ground Motion for Region 4(Charleston, SC Area) of 0.2 and 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-10 - MCE Ground Motion for Hawaii of 0.2 and 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-11 - MCE Ground Motion for Alaska of 0.2sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-12 - MCE Ground Motion for Alaska of 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-13 - MCE Ground Motion for Puerto Rico,Culebra,Vieques, St. Thomas, St. John and St. Croix of 0.2 and 1.0sec Spectral Response Acceleration");
      mapInfo.add("Figure 3.3-14 - MCE Ground Motion for Guam and Tutuila of 0.2 and 1.0sec Spectral Response Acceleration");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-01.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-02.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-03.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-04.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-05.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-06.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-07.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-08.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-09.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-10.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-11.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-12.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-13.pdf");
      mapFiles.add(mapURL_Path+"NEHRP-2003-Figure3.3-14.pdf");
    }

  }
  /**
   * Returns the supported maps info strings based on the selected region and
   * data edition.
   * @return String[]
   */
  public static String[] getSupportedMapInfo(){
    return (String[])mapInfo.toArray(new String[0]);
  }

  /**
   * Returns the URLs to actual map files.
   * @return String[]
   */
  public static String[] getSupportedMapFiles(){
    return  (String[])mapFiles.toArray(new String[0]);
  }

}
