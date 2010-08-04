package org.opensha.refFaultParamDb.calc.sectionDists;

import org.opensha.commons.util.threads.Task;

public class CalcTask implements Task {
	
	private FaultSectDistRecord record;
	private boolean fast;
	
	public CalcTask(FaultSectDistRecord record, boolean fast) {
		this.record = record;
		this.fast = fast;
	}

	@Override
	public void compute() {
		record.calcDistances(fast);
	}

}
