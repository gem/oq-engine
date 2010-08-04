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

import java.util.ArrayList;

import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.dao.db.ServerDB_Access;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ReadReferencesFromGoldenDB {
  private final static DB_AccessAPI dbConnPas= new DB_ConnectionPool();
  private final static DB_AccessAPI dbConnGolden = new ServerDB_Access(null);

  public ReadReferencesFromGoldenDB() {
  }

  public static void main(String[] args) {
    SessionInfo.setUserName("");
    SessionInfo.setPassword("");
    ReferenceDB_DAO refGoldenDAO = new ReferenceDB_DAO(dbConnGolden);
    ArrayList refList = refGoldenDAO.getAllReferences();
    ReferenceDB_DAO refPasDAO = new ReferenceDB_DAO(dbConnPas);
    for(int i=0; i<refList.size(); ++i) {
      System.out.println(i+" of "+refList.size());
      try {
        refPasDAO.addReference( (Reference) refList.get(i));
      }catch(Exception e) {
        System.out.println("Error in "+i);
      }
    }
  }

}
