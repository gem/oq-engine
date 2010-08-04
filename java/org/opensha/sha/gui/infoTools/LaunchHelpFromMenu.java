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

package org.opensha.sha.gui.infoTools;

import java.net.URL;

import javax.help.HelpBroker;
import javax.help.HelpSet;

/**
 * <p>Title: LaunchHelpFromMenu</p>
 *
 * <p>Description: This class allows the user to view the application help from the
 *  application's help menu.</p>
 * @author Nitin Gupta
 * @version 1.0
 */
public class LaunchHelpFromMenu {


		
    /**
     * Adding the help set file to launch the Scenario Shakemap help when user presses the Help from "Menu"
     * @param helpSetFileName String Name of the helpset file with full path
     */
    public HelpBroker createHelpMenu(String helpSetFileName){

       //ClassLoader cl = frame.getClass().getClassLoader();
       HelpSet hs = null;
       try {
    	   	//URL url = HelpSet.findHelpSet(cl, helpSetFileName);
    	   URL url = this.getClass().getResource(helpSetFileName);
    	   //System.out.println("URL ="+url);
    	   	//URL url = new URL(helpSetFileName);
         hs = new HelpSet(null, url);
       }
       catch (Exception ee) {
         ee.printStackTrace();
         return null;
       }
     // Create a HelpBroker object:
      return hs.createHelpBroker();
  }

/*public static void main(String args[]){
  LaunchHelpFromMenu helpMenu = new LaunchHelpFromMenu();
  HelpBroker hb = helpMenu.createHelpMenu("file:///Users/field/jbproject/sha/OpenSHA_docs/ScenarioShakeMap_UserManual/shaHelp.xml");
  //helpLaunchMenu.addActionListener(new CSH.DisplayHelpFromSource(hb));
}*/

}
