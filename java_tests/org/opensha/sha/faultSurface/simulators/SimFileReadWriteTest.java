package org.opensha.sha.faultSurface.simulators;

import static org.junit.Assert.*;

import java.util.ArrayList;

import org.junit.BeforeClass;
import org.junit.Test;

public class SimFileReadWriteTest {

	@BeforeClass
	public static void setUpBeforeClass() throws Exception {
	}
	
	@Test
	public void testWriteRead() {
		DeformationModelsToSimulators def2sim = new DeformationModelsToSimulators(82, false, 4.0);
		ArrayList<SimulatorFaultSurface> origSurfaces = def2sim.getSimulatorSurfaces();
		
		for (SimulatorFaultSurface surface : origSurfaces) {
			String origLine = surface.getElementLine();
			SimulatorFaultSurface newSurface = SimulatorFaultSurface.loadFromLine(origLine);
			String newLine = newSurface.getElementLine();
			System.out.println("Orig line:\t" + origLine);
			System.out.println("New line:\t" + newLine);
			
			SimulatorFaultSurface newSurface2 = SimulatorFaultSurface.loadFromLine(newLine);
			String newLine2 = newSurface.getElementLine();
			System.out.println("New line2:\t" + newLine);
			
			assertEquals("Lines don't match!", newLine, newLine2);
		}
	}

}
