package org.opensha.refFaultParamDb.calc.sectionDists;

import java.util.Comparator;
import java.util.Map;

public class RecordAveQuantityComparator implements Comparator<FaultSectDistRecord> {

	private Map<Integer, Double> idQuantityMap;
	
	private int mult;
	
	public RecordAveQuantityComparator(Map<Integer, Double> idQuantityMap, boolean smallestFirst) {
		this.idQuantityMap = idQuantityMap;
		
		if (smallestFirst)
			mult = 1;
		else
			mult = -1;
	}
	
	public void setMap(Map<Integer, Double> idQuantityMap) {
		this.idQuantityMap = idQuantityMap;
	}
	
	private RecordDistComparator distCompare = new RecordDistComparator();
	
	private double getAve(FaultSectDistRecord record) {
		double val1 = idQuantityMap.get(record.getID1());
		double val2 = idQuantityMap.get(record.getID2());
		
		return (val1 + val2) * 0.5d;
	}

	@Override
	public int compare(FaultSectDistRecord o1, FaultSectDistRecord o2) {
		double avg1 = getAve(o1);
		double avg2 = getAve(o2);
		
		boolean nan1 = Double.isNaN(avg1);
		boolean nan2 = Double.isNaN(avg2);
		
		if (nan1 && nan2)
			return distCompare.compare(o1, o2);
		if (nan1 && !nan2)
			return 1;
		if (!nan1 && nan2)
			return -1;
		
		if (avg1 < avg2)
			return -1 * mult;
		else if (avg1 > avg2)
			return 1 * mult;
		// they're equal
		
		return distCompare.compare(o1, o2);
	}

}
