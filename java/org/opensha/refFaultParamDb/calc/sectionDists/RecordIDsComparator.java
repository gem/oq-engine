package org.opensha.refFaultParamDb.calc.sectionDists;

import java.io.Serializable;
import java.util.Comparator;

public class RecordIDsComparator implements Comparator<FaultSectDistRecord>, Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	@Override
	public int compare(FaultSectDistRecord o1, FaultSectDistRecord o2) {
		if (o1.getID1() < o2.getID1())
			return -1;
		else if (o1.getID1() > o2.getID1())
			return 1;
		// they're equal
		if (o1.getID2() < o2.getID2())
			return -1;
		else if (o1.getID2() > o2.getID2())
			return 1;
		
		return 0;
	}

}
