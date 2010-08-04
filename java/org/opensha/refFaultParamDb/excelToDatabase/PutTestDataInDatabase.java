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

package org.opensha.refFaultParamDb.excelToDatabase;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;

/**
 * <p>Title: PutTestDataInDatabase.java </p>
 * <p>Description: Put the test data in  the database </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PutTestDataInDatabase {
  public PutTestDataInDatabase() {
  }

  public static void main(String[] args) {
    //PutTestDataInDatabase putTestDataInDatabase1 = new PutTestDataInDatabase();
    SessionInfo.setUserName(args[0]);
    SessionInfo.setPassword(args[1]);
    SessionInfo.setContributorInfo();
    //new ReadReferencesFile(); // put references in the database
    //new PutFaultNamesIntoDB(); // put fault names into database
    //new ReadSitesFile(); // put sites data in the database
    //new PutFaultSectionsIntoDatabase();
    //new PutCombinedInfoIntoDatabase_Qfault_Bird();
    
    
    
    //new PutPetrrizzoBirdDataIntoDatabase();
    //new PutCombinedInfoIntoDatabase_Qfault();
    //new PutCombinedInfoIntoDatabase_FAD();
    System.exit(0);
  }

}
