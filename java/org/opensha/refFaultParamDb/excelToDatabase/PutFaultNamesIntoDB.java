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

import java.util.HashMap;
import java.util.Iterator;

import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultDB_DAO;
import org.opensha.refFaultParamDb.vo.Fault;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PutFaultNamesIntoDB {
  private final static HashMap faultNameIdMapping = new HashMap();
  private final static FaultDB_DAO faultDAO = new FaultDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());

  public PutFaultNamesIntoDB() {
    Iterator it = faultNameIdMapping.keySet().iterator();
    while(it.hasNext()) {
      String faultName = (String)it.next();
      Integer faultId = (Integer)faultNameIdMapping.get(faultName);
      faultDAO.addFault(new Fault(faultId.intValue(),faultName) );
    }
  }

  static {
    faultNameIdMapping.put("Bartlett Springs fault system", new Integer(29));
    faultNameIdMapping.put("Black Mountain fault zone", new Integer(142));
    faultNameIdMapping.put("Calaveras fault zone", new Integer(54));
    faultNameIdMapping.put("Camp Rock-Emerson fault zone", new Integer(114));
    faultNameIdMapping.put("Cleghorn fault zone", new Integer(108));
    faultNameIdMapping.put("Concord fault", new Integer(38));
    faultNameIdMapping.put("Cordelia fault zone", new Integer(219));
    faultNameIdMapping.put("Elsinore fault zone", new Integer(126));
    faultNameIdMapping.put("Fish Lake Valley fault zone", new Integer(49));
    faultNameIdMapping.put("Fish Slough fault", new Integer(48));
    faultNameIdMapping.put("Garlock fault zone", new Integer(69));
    faultNameIdMapping.put("Green Valley fault", new Integer(37));
    faultNameIdMapping.put("Greenville fault zone", new Integer(53));
    faultNameIdMapping.put("Greenville fault zone", new Integer(53));
    faultNameIdMapping.put("Hayward fault zone", new Integer(55));
    faultNameIdMapping.put("Healdsburg fault", new Integer(31));
    faultNameIdMapping.put("Helendale-South Lockhart fault zone",
                           new Integer(110));
    faultNameIdMapping.put("Hilton Creek fault", new Integer(44));
    faultNameIdMapping.put("Hollywood fault", new Integer(102));
    faultNameIdMapping.put("Homestead Valley fault zone", new Integer(116));
    faultNameIdMapping.put("Honey Lake fault zone", new Integer(22));
    faultNameIdMapping.put("Hunting Creek-Berryessa fault system",
                           new Integer(35));
    faultNameIdMapping.put("Imperial fault", new Integer(132));
    faultNameIdMapping.put("Johnson Valley fault zone", new Integer(115));
    faultNameIdMapping.put("Lavic Lake fault", new Integer(351));
    faultNameIdMapping.put("Lenwood-Lockhart fault zone", new Integer(111));
    faultNameIdMapping.put("Little Lake fault zone", new Integer(72));
    faultNameIdMapping.put("Little Salmon fault zone", new Integer(15));
    faultNameIdMapping.put("Los Osos fault zone", new Integer(79));
    faultNameIdMapping.put("Maacama fault zone", new Integer(30));
    faultNameIdMapping.put("Mad River fault zone", new Integer(13));
    faultNameIdMapping.put("Malibu Coast fault zone", new Integer(99));
    faultNameIdMapping.put("Mesquite Lake fault", new Integer(123));
    faultNameIdMapping.put("Mohawk Valley fault zone", new Integer(25));
    faultNameIdMapping.put("Mono Lake fault", new Integer(41));
    faultNameIdMapping.put("Monte Vista-Shannon fault zone", new Integer(56));
    faultNameIdMapping.put("Newport-Inglewood-Rose Canyon fault zone",
                           new Integer(127));
    faultNameIdMapping.put("North Frontal thrust system", new Integer(109));
    faultNameIdMapping.put("Ortigalita fault zone", new Integer(52));
    faultNameIdMapping.put("Owens Valley fault zone", new Integer(51));
    faultNameIdMapping.put("Owl Lake fault", new Integer(70));
    faultNameIdMapping.put("Palos Verdes fault zone", new Integer(128));
    faultNameIdMapping.put("Panamint Valley fault zone", new Integer(67));
    faultNameIdMapping.put("Pisgah-Bullion fault zone", new Integer(122));
    faultNameIdMapping.put("Pleito fault zone", new Integer(76));
    faultNameIdMapping.put("Raymond fault", new Integer(103));
    faultNameIdMapping.put("Rodgers Creek fault", new Integer(32));
    faultNameIdMapping.put("San Andreas fault zone", new Integer(1));
    faultNameIdMapping.put("San Gabriel fault", new Integer(89));
    faultNameIdMapping.put("San Gregorio fault zone", new Integer(60));
    faultNameIdMapping.put("San Jacinto fault zone", new Integer(125));
    faultNameIdMapping.put("San Simeon fault", new Integer(80));
    faultNameIdMapping.put("Santa Monica fault", new Integer(101));
    faultNameIdMapping.put("Santa Ynez fault zone", new Integer(87));
    faultNameIdMapping.put("Sargent fault zone", new Integer(58));
    faultNameIdMapping.put("Sierra Madre fault zone", new Integer(105));
    faultNameIdMapping.put("Simi-Santa Rosa fault zone", new Integer(98));
    faultNameIdMapping.put("Zayante-Vergeles fault zone", new Integer(59));
  }


}
