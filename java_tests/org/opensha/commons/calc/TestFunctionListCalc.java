package org.opensha.commons.calc;

import org.junit.Test;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;

import static org.junit.Assert.*;

public class TestFunctionListCalc {
	
	private ArbitrarilyDiscretizedFunc func1 = new ArbitrarilyDiscretizedFunc();
	private ArbitrarilyDiscretizedFunc func2 = new ArbitrarilyDiscretizedFunc();
	private ArbitrarilyDiscretizedFunc func3 = new ArbitrarilyDiscretizedFunc();

	public TestFunctionListCalc() {
		
		func1.set(1d, 5d);
		func1.set(2d, 5d);
		func1.set(3d, 5d);
		func1.set(4d, 5d);
		func1.set(5d, 5d);
		
		func2.set(1d, 10d);
		func2.set(2d, 10d);
		func2.set(3d, 10d);
		func2.set(4d, 10d);
		func2.set(5d, 10d);
		
		func3.set(1d, 1d);
		func3.set(2d, 2d);
		func3.set(3d, 3d);
		func3.set(4d, 4d);
		func3.set(5d, 5d);
	}

	@Test
	public void testSum1_2() {
		DiscretizedFuncList list = new DiscretizedFuncList();
		list.add(func1);
		list.add(func2);
		
		DiscretizedFunc mean = FunctionListCalc.getMean(list);
		
		for (int i=0; i<5; i++) {
			assertTrue(mean.getY(i) == 7.5);
		}
	}
	
	@Test
	public void testSum1_2_3() {
		DiscretizedFuncList list = new DiscretizedFuncList();
		list.add(func1);
		list.add(func2);
		list.add(func3);
		
		DiscretizedFunc mean = FunctionListCalc.getMean(list);
		
		for (int i=0; i<5; i++) {
			assertTrue(mean.getY(i) == (5 + 10 + i + 1) / 3d);
		}
	}

}
