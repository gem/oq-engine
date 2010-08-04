package org.opensha.refFaultParamDb.calc.sectionDists;

import java.util.Comparator;

public class RecordDistComparator implements Comparator<FaultSectDistRecord> {
	
	private RecordIDsComparator idCompare = new RecordIDsComparator();

	@Override
	public int compare(FaultSectDistRecord o1, FaultSectDistRecord o2) {
		if (o1.getMinDist() < o2.getMinDist())
			return -1;
		else if (o1.getMinDist() > o2.getMinDist())
			return 1;
		// they're equal
		
		return idCompare.compare(o1, o2);
	}

}
