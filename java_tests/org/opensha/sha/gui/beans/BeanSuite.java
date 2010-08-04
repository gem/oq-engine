package org.opensha.sha.gui.beans;

import org.junit.runner.RunWith;
import org.junit.runners.Suite;
import org.opensha.commons.calc.CalcSuite;

@RunWith(Suite.class)
@Suite.SuiteClasses({
	TestIMR_MultiGuiBean.class,
	TestIMT_NewGuiBean.class,
	TestIMT_IMR_Interactions.class
})

public class BeanSuite {

	public static void main(String args[])
	{
		org.junit.runner.JUnitCore.runClasses(CalcSuite.class);
	}

}
