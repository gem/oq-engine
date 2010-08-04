/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2;

import java.util.ArrayList;

import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.A_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.B_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelSummaryFinal;

/**
 * This class gets B-Faults for Mean UCERF ERF.
 * It finds the B-Faults which are unique/common, connected/unconnected in D2.1 and D2.4
 * 
 * 
 * @author vipingupta
 *
 */
public class B_FaultsFetcherForMeanUCERF {

	private ArrayList<FaultSegmentData> faultSegmentDataList2_1_Unconn; 
	private ArrayList<FaultSegmentData> faultSegmentDataList2_1_Conn;
	private ArrayList<FaultSegmentData> faultSegmentDataList2_2_Unconn;
	private ArrayList<FaultSegmentData> faultSegmentDataList2_2_Conn;
	private ArrayList<String> faultNamesList2_1_Unconn, faultNamesList2_1_Conn, participatingFaultNamesList2_1_Conn;
	private ArrayList<String> faultNamesList2_2_Unconn, faultNamesList2_2_Conn, participatingFaultNamesList2_2_Conn;
	
	public B_FaultsFetcherForMeanUCERF(A_FaultsFetcher aFaultsFetcher, boolean isAseisReducesArea) {
		
		// get deformation model summaries
//		DeformationModelSummaryDB_DAO defModelSummaryDAO = new DeformationModelSummaryDB_DAO(DB_AccessAPI.dbConnection);
		DeformationModelSummaryFinal defModelSummaryDAO = new DeformationModelSummaryFinal();
		DeformationModelSummary defModelSummary2_1 = defModelSummaryDAO.getDeformationModel("D2.1");
		DeformationModelSummary defModelSummary2_2 = defModelSummaryDAO.getDeformationModel("D2.4");

		B_FaultsFetcher bFaultsFetcher = new B_FaultsFetcher();
		
		// 2.1 and Unconnected
		aFaultsFetcher.setDeformationModel(defModelSummary2_1, false);
		bFaultsFetcher.setDeformationModel(false, defModelSummary2_1, aFaultsFetcher);
		faultSegmentDataList2_1_Unconn = bFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
		faultNamesList2_1_Unconn = bFaultsFetcher.getAllFaultNames();
		
		
		//2.1 and connected
		bFaultsFetcher.setDeformationModel(true, defModelSummary2_1, aFaultsFetcher);
		faultSegmentDataList2_1_Conn = bFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
		faultNamesList2_1_Conn = bFaultsFetcher.getAllFaultNames();
		participatingFaultNamesList2_1_Conn = bFaultsFetcher.getConnectedFaultSectionsNamesList();
		// Retain connected faults only
		faultNamesList2_1_Conn.removeAll(faultNamesList2_1_Unconn);
		faultNamesList2_1_Unconn.removeAll(participatingFaultNamesList2_1_Conn);
		faultNamesList2_1_Conn.addAll(participatingFaultNamesList2_1_Conn);

		// 2.4 and unconnected
		aFaultsFetcher.setDeformationModel(defModelSummary2_2, false);
		bFaultsFetcher.setDeformationModel(false, defModelSummary2_2, aFaultsFetcher);
		faultSegmentDataList2_2_Unconn = bFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
		faultNamesList2_2_Unconn = bFaultsFetcher.getAllFaultNames();
		
		//2.4 and connected
		bFaultsFetcher.setDeformationModel(true, defModelSummary2_2, aFaultsFetcher);
		faultSegmentDataList2_2_Conn = bFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);
		faultNamesList2_2_Conn = bFaultsFetcher.getAllFaultNames();
		participatingFaultNamesList2_2_Conn = bFaultsFetcher.getConnectedFaultSectionsNamesList();

		//  Retain connected faults only
		faultNamesList2_2_Conn.removeAll(faultNamesList2_2_Unconn);
		faultNamesList2_2_Unconn.removeAll(participatingFaultNamesList2_2_Conn);
		faultNamesList2_2_Conn.addAll(participatingFaultNamesList2_2_Conn);

	}
	
	
	/**
	 * Retun a list of All common B-Faults between F2.1 and F2.2 
	 * when "More B-Faults connection" paramter is set to False n UCERF2
	 */
	public ArrayList<FaultSegmentData> getB_FaultsCommonNoConnOpts() {
		ArrayList<String> commonNames = new ArrayList<String>();
		commonNames.addAll(faultNamesList2_1_Unconn);
		commonNames.retainAll(faultNamesList2_2_Unconn);
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();
		for(int i=0; i<faultSegmentDataList2_1_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Unconn.get(i);
			if(commonNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		return commonSegmentDataList;
	}
	
	/**
	 * Retun a list of Unique  B-Faults for F2.1 
	 * when "More B-Faults connection" paramter is set to False n UCERF2
	 */
	public ArrayList<FaultSegmentData> getB_FaultsUniqueToF2_1NoConnOpts() {
		ArrayList<String> uniqueNames = new ArrayList<String>();
		uniqueNames.addAll(faultNamesList2_1_Unconn);
		uniqueNames.removeAll(faultNamesList2_2_Unconn);
		uniqueNames.removeAll(faultNamesList2_2_Conn);
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();
		for(int i=0; i<faultSegmentDataList2_1_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Unconn.get(i);
			if(uniqueNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		return commonSegmentDataList;
	}
	
	/**
	 * Retun a list of Unique  B-Faults for F2.2 
	 * when "More B-Faults connection" paramter is set to False n UCERF2
	 */
	public ArrayList<FaultSegmentData> getB_FaultsUniqueToF2_2NoConnOpts() {
		ArrayList<String> uniqueNames = new ArrayList<String>();
		uniqueNames.addAll(faultNamesList2_2_Unconn);
		uniqueNames.removeAll(faultNamesList2_1_Unconn);
		uniqueNames.removeAll(faultNamesList2_1_Conn);
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();
		for(int i=0; i<faultSegmentDataList2_2_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_2_Unconn.get(i);
			if(uniqueNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		return commonSegmentDataList;
	}
	
	/**
	 * Retun a list of Unique  B-Faults for F2.1 
	 * when "More B-Faults connection" paramter is set to False n UCERF2
	 */
	public ArrayList<FaultSegmentData> getB_FaultsUniqueToF2_1ConnOpts() {
		ArrayList<String> uniqueNames = new ArrayList<String>();
		uniqueNames.addAll(faultNamesList2_1_Conn);
		uniqueNames.removeAll(faultNamesList2_2_Conn);
		uniqueNames.removeAll(faultNamesList2_2_Unconn);
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();
		for(int i=0; i<faultSegmentDataList2_1_Conn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Conn.get(i);
			if(uniqueNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		for(int i=0; i<faultSegmentDataList2_1_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Unconn.get(i);
			if(uniqueNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		return commonSegmentDataList;
	}
	
	/**
	 * Retun a list of Unique  B-Faults for F2.2 
	 * when "More B-Faults connection" paramter is set to False n UCERF2
	 */
	public ArrayList<FaultSegmentData> getB_FaultsUniqueToF2_2ConnOpts() {
		ArrayList<String> uniqueNames = new ArrayList<String>();
		uniqueNames.addAll(faultNamesList2_2_Conn);
		uniqueNames.removeAll(faultNamesList2_1_Conn);
		uniqueNames.removeAll(faultNamesList2_1_Unconn);
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();
		for(int i=0; i<faultSegmentDataList2_2_Conn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_2_Conn.get(i);
			if(uniqueNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		
		for(int i=0; i<faultSegmentDataList2_2_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_2_Unconn.get(i);
			if(uniqueNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		return commonSegmentDataList;
	}
	
	/**
	 * Retun a list of Connected common B-Faults between F2.1 and F2.2 
	 * when "More B-Faults connection" paramter is set to True in UCERF2
	 */
	public ArrayList<FaultSegmentData> getB_FaultsCommonConnOpts() {
		ArrayList<String> commonNames = new ArrayList<String>();
		commonNames.addAll(faultNamesList2_1_Conn);
		commonNames.retainAll(faultNamesList2_2_Conn);
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();
		for(int i=0; i<faultSegmentDataList2_1_Conn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Conn.get(i);
			if(commonNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		for(int i=0; i<faultSegmentDataList2_1_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Unconn.get(i);
			if(commonNames.contains(faultSegmentData.getFaultName()))
				commonSegmentDataList.add(faultSegmentData);
		}
		return commonSegmentDataList;
	}
	
	/**
	 * Retun a list of  B-Faults that are common to both fault models
	 * but are connected in one and not connected in the other
	 */
	public ArrayList<FaultSegmentData> getB_FaultsCommonWithUniqueConnOpts() {
		
		
		// 2.1 names
		ArrayList<String> conn2_1Names = new ArrayList<String>();
		conn2_1Names.addAll(faultNamesList2_1_Conn);
		conn2_1Names.removeAll(faultNamesList2_2_Conn);
		conn2_1Names.retainAll(faultNamesList2_2_Unconn);
		
		// 2.2 names
		ArrayList<String> conn2_2Names = new ArrayList<String>();
		conn2_2Names.addAll(faultNamesList2_2_Conn);
		conn2_2Names.removeAll(faultNamesList2_1_Conn);
		conn2_2Names.retainAll(faultNamesList2_1_Unconn);
		
		ArrayList<String> commonWithUniqueConnNames = new ArrayList<String>();
		commonWithUniqueConnNames.addAll(conn2_1Names);
		commonWithUniqueConnNames.addAll(conn2_2Names);
		
		ArrayList<FaultSegmentData> commonSegmentDataList = new ArrayList<FaultSegmentData>();

		for(int i=0; i<faultSegmentDataList2_2_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_2_Unconn.get(i);
			if(commonWithUniqueConnNames.contains(faultSegmentData.getFaultName())){
				commonSegmentDataList.add(faultSegmentData);
				commonWithUniqueConnNames.remove(faultSegmentData.getFaultName());
			}
		}
		
		for(int i=0; i<faultSegmentDataList2_1_Unconn.size(); ++i) {
			FaultSegmentData faultSegmentData = faultSegmentDataList2_1_Unconn.get(i);
			if(commonWithUniqueConnNames.contains(faultSegmentData.getFaultName())){
				commonSegmentDataList.add(faultSegmentData);
				commonWithUniqueConnNames.remove(faultSegmentData.getFaultName());
			}
		}
		
		return commonSegmentDataList;
	}
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		A_FaultsFetcher aFaultsFetcher = new A_FaultsFetcher();
//		DeformationModelSummaryDB_DAO defModelSummaryDAO = new DeformationModelSummaryDB_DAO(DB_AccessAPI.dbConnection);
		DeformationModelSummaryFinal defModelSummaryDAO = new DeformationModelSummaryFinal();
		DeformationModelSummary defModelSummary2_1 = defModelSummaryDAO.getDeformationModel("D2.1");
		aFaultsFetcher.setDeformationModel(defModelSummary2_1, false);
		
		B_FaultsFetcherForMeanUCERF bFaultsFetcher = new B_FaultsFetcherForMeanUCERF(aFaultsFetcher, true);
		
		ArrayList<FaultSegmentData> faultSegDataList = bFaultsFetcher.getB_FaultsCommonConnOpts();
		System.out.println("********Common with Connections:");
		for(int i=0; i<faultSegDataList.size(); ++i) System.out.println(faultSegDataList.get(i).getFaultName());
		
		faultSegDataList  = bFaultsFetcher.getB_FaultsCommonNoConnOpts();
		System.out.println("********Common with No Connections:");
		for(int i=0; i<faultSegDataList.size(); ++i) System.out.println(faultSegDataList.get(i).getFaultName());
		
		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_1ConnOpts();
		System.out.println("********Unique to 2.1 with Connections:");
		for(int i=0; i<faultSegDataList.size(); ++i) System.out.println(faultSegDataList.get(i).getFaultName());

		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_1NoConnOpts();
		System.out.println("********Unique to 2.1 with No Connections:");
		for(int i=0; i<faultSegDataList.size(); ++i) System.out.println(faultSegDataList.get(i).getFaultName());

		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_2ConnOpts();
		System.out.println("********Unique to 2.2 with Connections:");
		for(int i=0; i<faultSegDataList.size(); ++i) System.out.println(faultSegDataList.get(i).getFaultName());

		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_2NoConnOpts();
		System.out.println("********Unique to 2.2 with No Connections:");
		for(int i=0; i<faultSegDataList.size(); ++i) System.out.println(faultSegDataList.get(i).getFaultName());

		
		
	}

}
