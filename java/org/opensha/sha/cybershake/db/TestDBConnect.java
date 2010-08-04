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

package org.opensha.sha.cybershake.db;
import java.sql.ResultSet;
import java.sql.SQLException;



public class TestDBConnect {

	public static void main(String[] args) {
		DBAccess dbc = new DBAccess("surface.usc.edu","CyberShake");
		ResultSet rs = null;
		try {
			rs = dbc.selectData("SHOW TABLES");
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		
		//dbc.deleteOrUpdateData("Delete from ERF_Metadata");
		//try {
		//	dbc.insertUpdateOrDeleteData("Delete from CyberShake_Site_Ruptures");
		//} catch (SQLException e1) {
			// TODO Auto-generated catch block
			//e1.printStackTrace();
		//}
		//try {
			//dbc.insertUpdateOrDeleteData("Delete from CyberShake_Site_Regions");
		//} catch (SQLException e1) {
			// TODO Auto-generated catch block
			//e1.printStackTrace();
		//}
		//dbc.deleteOrUpdateData("Delete from Ruptures");
		//dbc.deleteOrUpdateData("Delete from Points");	
		try {
			dbc.insertUpdateOrDeleteData("Delete from CyberShake_Sites");
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		//dbc.deleteOrUpdateData("Delete from ERF_IDs");
		try {
			System.out.println(rs.getMetaData().getColumnCount());
			rs.first();
			while (!rs.isAfterLast()) {
				System.out.println(rs.getString(1));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}
}

