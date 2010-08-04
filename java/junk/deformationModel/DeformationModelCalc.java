package junk.deformationModel;

import java.util.ArrayList;

import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;

/**
 * It compares the plot for the fault sections vs the GPS data 
 * 
 * @author vipingupta
 *
 */
public class DeformationModelCalc {
	// fault section info from the database
	private PrefFaultSectionDataDB_DAO prefFaultSectionDAO = 
		new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private final static int NUM = 50;

	/**
	 * Get the distance and cumulative slip function given a cross section
	 * 
	 * @param eastLoc East location of the cross section
	 * @param westLoc West Location of the cross Section
	 * @return
	 */
	public DiscretizedFuncAPI getDistanceSlipFunc(Location eastLoc, Location westLoc) {
		EvenlyDiscretizedFunc evenlyDiscFunc = new EvenlyDiscretizedFunc(0, 
				LocationUtils.horzDistanceFast(eastLoc, westLoc),
				NUM);
		double delta = evenlyDiscFunc.getDelta();
		ArrayList faultSectionPrefDataList = prefFaultSectionDAO.getAllFaultSectionPrefData();
		LineIntersection lineInterSection = new LineIntersection();
		double x,y, rtLateralSlipComp;
		for(int i=0; i<faultSectionPrefDataList.size(); ++i) {
			FaultSectionPrefData faultSectionPrefData = (FaultSectionPrefData)faultSectionPrefDataList.get(i);
			//System.out.println(faultSectionPrefData.getSectionName());
			// find whether this fault section cuts the cross section
			Location intesectionLocation = lineInterSection.getIntersectionPoint(eastLoc, westLoc, faultSectionPrefData.getFaultTrace());
			// if this fault section does not cut the cross section
			if(intesectionLocation==null) continue;
			rtLateralSlipComp = getRightLateralSlipComp(faultSectionPrefData);
			// if slip or rake is not available
			if(rtLateralSlipComp==0 || Double.isNaN(rtLateralSlipComp)) {
				System.out.println(faultSectionPrefData.getSectionName()+" intersects but its slip is 0");
				continue;
			}
			System.out.println("*********"+faultSectionPrefData.getSectionName()+" intersects************** at "+intesectionLocation);
			System.out.println(rtLateralSlipComp +","+faultSectionPrefData.getAveRake()+","+lineInterSection.getStrike());
			x= Math.ceil(lineInterSection.getDistance()/delta)*delta; 
			y = evenlyDiscFunc.getY(x);
			System.out.println(x+","+y);
			evenlyDiscFunc.set(x, y+rtLateralSlipComp*Math.cos(Math.toRadians(lineInterSection.getStrike())));
			y = evenlyDiscFunc.getY(x);
			System.out.println(x+","+y);
		}
		EvenlyDiscretizedFunc cumFunc = getCumFunc(evenlyDiscFunc);
		return cumFunc;
	}
	
	/**
	 * Get the cumulative function
	 * 
	 * @param func
	 * @return
	 */
	private EvenlyDiscretizedFunc getCumFunc(EvenlyDiscretizedFunc func) {
		EvenlyDiscretizedFunc cumFunc = new EvenlyDiscretizedFunc(func.getMinX(), func.getMaxX(), func.getNum());
		cumFunc.set(0, func.getY(0));
		for(int i=1; i<cumFunc.getNum(); ++i) {
			cumFunc.set(i, cumFunc.getY(i-1)+func.getY(i));
		}
		return cumFunc;
	}
	
	
	/**
	 * Get Right Lateral component of slip
	 * 
	 * @param faultSectionPrefData
	 * @return
	 */
	private double getRightLateralSlipComp(FaultSectionPrefData faultSectionPrefData ) {
		double rake = faultSectionPrefData.getAveRake();
		double slip = faultSectionPrefData.getAveLongTermSlipRate();
		if(Double.isNaN(rake)) return 0;
		if(0<=rake && rake<=180) return slip*Math.cos(Math.toRadians(180-rake));
		if(180<=rake && rake<=0) return -1*slip*Math.cos(Math.toRadians(180+rake));
		return 0;
	}
	
	
	public static void main(String args[]) {
		Location loc1 = new Location(34, -118);
		Location loc2 = new Location(34, -117);
		DeformationModelCalc calc = new DeformationModelCalc();
		DiscretizedFuncAPI func = calc.getDistanceSlipFunc(loc1, loc2);
		System.out.println(func);
	}
}
