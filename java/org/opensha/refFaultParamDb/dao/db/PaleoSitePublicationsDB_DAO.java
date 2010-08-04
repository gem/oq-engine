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

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;

/**
 * <p>Title: PaleoSitePublicationsDB_DAO.java </p>
 * <p>Description: It puts the site type name and representative strand index associated
 * with each publication into the database </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PaleoSitePublicationsDB_DAO {
	private final static String TABLE_NAME = "Paleo_Site_Publications";
	private final static String SITE_ID = "Site_Id";
	private final static String SITE_ENTRY_DATE = "Site_Entry_Date";
	private final static String ENTRY_DATE = "Entry_Date";
	private final static String SITE_TYPE_ID = "Site_Type_Id";
	private final static String REPRESENTATIVE_STRAND_INDEX =
		"Representative_Strand_Index";
	private final static String REFERENCE_ID = "Reference_Id";
	private final static String CONTRIBUTOR_ID = "Contributor_Id";
	private DB_AccessAPI dbAccess;
	// site representation DAO
	private SiteRepresentationDB_DAO siteRepresentationDAO;
	// site type DAO
	private SiteTypeDB_DAO siteTypeDAO;
	// reference DAO
	private ReferenceDB_DAO referenceDAO;
	// contributor DAO
	private ContributorDB_DAO contributorDAO;
	public PaleoSitePublicationsDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
		siteRepresentationDAO = new SiteRepresentationDB_DAO(dbAccess);
		siteTypeDAO = new SiteTypeDB_DAO(dbAccess);
		referenceDAO = new ReferenceDB_DAO(dbAccess);
		contributorDAO = new ContributorDB_DAO(dbAccess);
	}

	/**
	 * Insert the publication, site type and representative site index into the
	 * database
	 * @param paleoSitePublication
	 */
	public void addPaleoSitePublicationInfo(PaleoSitePublication paleoSitePublication) {
		String systemDate;
		try { // get the current system date
			systemDate = dbAccess.getSystemDate();
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
		// site representation index
		int siteRepIndex = this.siteRepresentationDAO.getSiteRepresentation(paleoSitePublication.getRepresentativeStrandName()).getSiteRepresentationId();
		// site types associated with this site
		ArrayList<String> siteTypeNames = paleoSitePublication.getSiteTypeNames();
		try {
			for(int i=0; i<siteTypeNames.size(); ++i) {
				int siteTypeId = this.siteTypeDAO.getSiteType(siteTypeNames.get(i)).getSiteTypeId();
				String sql = "insert into "+TABLE_NAME+"("+SITE_ID+","+SITE_ENTRY_DATE+","+
				ENTRY_DATE+","+SITE_TYPE_ID+","+REPRESENTATIVE_STRAND_INDEX+","+CONTRIBUTOR_ID+","+
				REFERENCE_ID+") "+
				"values ("+paleoSitePublication.getSiteId()+",'"+
				paleoSitePublication.getSiteEntryDate()+"','"+
				systemDate+"',"+siteTypeId+","+siteRepIndex+","+
				SessionInfo.getContributor().getId()+","+paleoSitePublication.getReference().getReferenceId()+")";
				//System.out.println(sql);
				dbAccess.insertUpdateOrDeleteData(sql);
			}
		} catch(SQLException e) {
			e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 * Get all the publications for a particular site
	 * @param siteId
	 * @return
	 */
	public ArrayList<PaleoSitePublication> getPaleoSitePublicationInfo(int siteId) {
		String condition = " where "+SITE_ID+"="+siteId;
		return query(condition);
	}

	/**
	 * Query the database
	 * @param condition
	 * @return
	 */
	private ArrayList<PaleoSitePublication> query(String condition) {
		ArrayList<PaleoSitePublication> paleoSitePubList = new ArrayList<PaleoSitePublication>();
		String sql =  "select "+SITE_ID+",to_char("+SITE_ENTRY_DATE+") as "+SITE_ENTRY_DATE+","+
		"to_char("+ENTRY_DATE+") as "+ENTRY_DATE+","+
		SITE_TYPE_ID+","+REPRESENTATIVE_STRAND_INDEX+","+CONTRIBUTOR_ID+","+
		REFERENCE_ID+" from "+TABLE_NAME+condition;
		HashMap<Integer, PaleoSitePublication> refIdPublicationMap = new HashMap<Integer, PaleoSitePublication>();
		try {
			ResultSet rs  = dbAccess.queryData(sql);
			while(rs.next())  {
				int referenceId = rs.getInt(REFERENCE_ID);
				String siteTypeName = this.siteTypeDAO.getSiteType(rs.getInt(
						SITE_TYPE_ID)).getSiteType();
				String contributorName = this.contributorDAO.getContributor(rs.getInt(CONTRIBUTOR_ID)).getName();
				PaleoSitePublication paleoSitePublication;
				// if we encounter the same publication again
				if (refIdPublicationMap.containsKey(new Integer(referenceId))) {
					paleoSitePublication = (PaleoSitePublication) refIdPublicationMap.get(new
							Integer(referenceId));
					paleoSitePublication.setContributorName(contributorName);
					paleoSitePublication.setEntryDate(rs.getString(ENTRY_DATE));
					ArrayList<String> siteTypeNames = paleoSitePublication.getSiteTypeNames();
					if (!siteTypeNames.contains(siteTypeName))
						siteTypeNames.add(siteTypeName);
				}
				else { // if we encounter the publication for the first time for this site
					paleoSitePublication = new PaleoSitePublication();
					paleoSitePublication.setSiteId(rs.getInt(SITE_ID));
					paleoSitePublication.setSiteEntryDate(rs.getString(SITE_ENTRY_DATE));
					paleoSitePublication.setContributorName(contributorName);
					paleoSitePublication.setEntryDate(rs.getString(ENTRY_DATE));
					paleoSitePublication.setRepresentativeStrandName(this.siteRepresentationDAO.getSiteRepresentation(rs.getInt(REPRESENTATIVE_STRAND_INDEX)).getSiteRepresentationName());
					ArrayList<String> siteTypeNames = new ArrayList<String>();
					siteTypeNames.add(siteTypeName);
					paleoSitePublication.setSiteTypeNames(siteTypeNames);
					paleoSitePublication.setReference(referenceDAO.getReference(rs.getInt(REFERENCE_ID)));
					paleoSitePubList.add(paleoSitePublication);
					refIdPublicationMap.put(new Integer(rs.getInt(REFERENCE_ID)), paleoSitePublication);
				}
			}
			rs.close();
		} catch(SQLException e) {
			e.printStackTrace();
			throw new QueryException(e.getMessage());
		}
		return paleoSitePubList;
	}


}
