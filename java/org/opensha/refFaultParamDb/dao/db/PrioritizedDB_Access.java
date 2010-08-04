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

package org.opensha.refFaultParamDb.dao.db;

import java.sql.SQLException;
import java.util.ArrayList;

import oracle.spatial.geometry.JGeometry;


import com.sun.rowset.CachedRowSetImpl;

/**
 * This class represents a list of DB_AccessAPI's. The first one that works will be used
 * for all connections. This is ideal for the case where you would prefer a direct DB
 * connection, but it might be blocked by a firewall, in which case you fall back to a
 * servlet brokered connection.
 * 
 * @author kevin
 *
 */
public class PrioritizedDB_Access implements DB_AccessAPI {

	private static final boolean D = false;

	private DB_AccessAPI dbAccess = null;

	public static ArrayList<DB_AccessAPI> createDB2ReadOnlyAccessors() {
		ArrayList<DB_AccessAPI> accessors = new ArrayList<DB_AccessAPI>();
		// first priority is a direct connection
		try {
			accessors.add(new DB_ConnectionPool(DB_ConnectionPool.db_prop_2_file));
		} catch (Throwable t) {
			t.printStackTrace();
		}
		// if that doesn't work we'll try the servlet to get around firewall issues
		try {
			accessors.add(new ServerDB_Access(ServerDB_Access.SERVLET_URL_DB2));
		} catch (Throwable t) {
			t.printStackTrace();
		}
		return accessors;
	}

	public static ArrayList<DB_AccessAPI> createDB3ReadOnlyAccessors() {
		ArrayList<DB_AccessAPI> accessors = new ArrayList<DB_AccessAPI>();
		// first priority is a direct connection
		try {
			accessors.add(new DB_ConnectionPool(DB_ConnectionPool.db_prop_3_ro_file));
		} catch (Throwable t) {
			t.printStackTrace();
		}
		// if that doesn't work we'll try the servlet to get around firewall issues
		try {
			accessors.add(new ServerDB_Access(ServerDB_Access.SERVLET_URL_DB3));
		} catch (Throwable t) {
			t.printStackTrace();
		}
		return accessors;
	}

	public PrioritizedDB_Access(ArrayList<DB_AccessAPI> accessors) {
		for (int i=0; i<accessors.size(); i++) {
			DB_AccessAPI accessor = accessors.get(i);
			boolean success = isAccessorValid(accessor);
			if (success) {
				if (D) System.out.println("DB Accessor " + (i+1) + " successful!");
				dbAccess = accessor;
				break;
			} else {
				System.err.println("DB Accessor " + (i+1) + "/" + accessors.size() + " failed (see above stack trace).");
			}
		}
		if (dbAccess == null) {
			throw new RuntimeException("No valid DB Accessors! (0/" + accessors.size() + " successful)");
		}
	}

	public static boolean isAccessorValid(DB_AccessAPI dbAccess) {
		String sql = "SELECT * FROM Fault_Model where rownum<=1";
		try {
			CachedRowSetImpl rs = dbAccess.queryData(sql);
			rs.first();
		} catch (Throwable t) {
			t.printStackTrace();
			return false;
		}
		return true;
	}

	public int getNextSequenceNumber(String sequenceName) throws SQLException {
		return dbAccess.getNextSequenceNumber(sequenceName);
	}

	public String getSystemDate() throws SQLException {
		return dbAccess.getSystemDate();
	}

	public int insertUpdateOrDeleteData(String sql) throws SQLException {
		return dbAccess.insertUpdateOrDeleteData(sql);
	}

	public int insertUpdateOrDeleteData(String sql, ArrayList<JGeometry> geometryList)
	throws SQLException {
		return dbAccess.insertUpdateOrDeleteData(sql, geometryList);
	}

	public CachedRowSetImpl queryData(String sql) throws SQLException {
		return dbAccess.queryData(sql);
	}

	public SpatialQueryResult queryData(String sqlWithSpatialColumnNames,
			String sqlWithNoSpatialColumnNames, ArrayList<String> spatialColumnNames)
	throws SQLException {
		return dbAccess.queryData(sqlWithSpatialColumnNames, sqlWithNoSpatialColumnNames, spatialColumnNames);
	}

	public int resetPasswordByEmail(String sql) throws SQLException {
		return dbAccess.resetPasswordByEmail(sql);
	}

	public static void main(String args[]) {
		new PrioritizedDB_Access(PrioritizedDB_Access.createDB2ReadOnlyAccessors());
		System.exit(0);
	}

}
