package org.opensha.sha.gui.beans;


import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Stack;

import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.util.ListUtils;
import org.opensha.gem.GEM1.scratch.ZhaoEtAl_2006_AttenRel;
import org.opensha.sha.gui.beans.event.IMTChangeEvent;
import org.opensha.sha.gui.beans.event.IMTChangeListener;
import org.opensha.sha.gui.infoTools.AttenuationRelationshipsInstance;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CY_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.TectonicRegionType;

public class TestIMT_NewGuiBean implements IMTChangeListener {

	static ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs;

	Stack<IMTChangeEvent> eventStack = new Stack<IMTChangeEvent>();

	IMT_NewGuiBean gui;

	@BeforeClass
	public static void setUpBeforeClass() {
		AttenuationRelationshipsInstance inst = new AttenuationRelationshipsInstance();
		imrs = inst.createIMRClassInstance(null);
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			imr.setParamDefaults();
		}
	}

	@Before
	public void setUp() throws Exception {
		gui = new IMT_NewGuiBean(imrs);
	}

	@Test
	public void testIMTList() {
		ArrayList<String> supportedIMTs = gui.getSupportedIMTs();
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			for (ParameterAPI<?> imtParam : imr.getSupportedIntensityMeasuresList()) {
				String imtName = imtParam.getName();
				assertTrue("IMT '" + imtName + "' should be in list!",
						supportedIMTs.contains(imtName));
			}
		}
	}

	@Test
	public void testShowsAllPeriods() {
		gui.setSelectedIMT(SA_Param.NAME);
		assertTrue("SA im should be instance of SA_Param", gui.getSelectedIM() instanceof SA_Param);
		SA_Param saParam = (SA_Param) gui.getSelectedIM();
		PeriodParam periodParam = saParam.getPeriodParam();

		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			if (!imr.isIntensityMeasureSupported(SA_Param.NAME))
				continue;
			imr.setIntensityMeasure(SA_Param.NAME);
			SA_Param mySAParam = (SA_Param) imr.getIntensityMeasure();
			PeriodParam myPeriodParam = mySAParam.getPeriodParam();
			for (Double period : myPeriodParam.getAllowedDoubles()) {
				assertTrue("Period '" + period + "' should be supported!", periodParam.isAllowed(period));
			}
		}
	}

	@Test
	public void testShowsSupportedPeriods() {
		gui.setSelectedIMT(SA_Param.NAME);
		assertTrue("SA im should be instance of SA_Param", gui.getSelectedIM() instanceof SA_Param);
		SA_Param saParam = (SA_Param) gui.getSelectedIM();
		PeriodParam periodParam = saParam.getPeriodParam();

		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			if (!imr.isIntensityMeasureSupported(SA_Param.NAME))
				continue;
			imr.setIntensityMeasure(SA_Param.NAME);
			SA_Param mySAParam = (SA_Param) imr.getIntensityMeasure();
			PeriodParam myPeriodParam = mySAParam.getPeriodParam();

			gui.setSupportedPeriods(myPeriodParam.getSupportedPeriods());

			for (Double period : periodParam.getAllowedDoubles()) {
				assertTrue("Period '" + period + "' should be supported!", myPeriodParam.isAllowed(period));
			}
		}
	}

	@Test
	public void testIMTChangeEvents() {
		gui.setSelectedIMT(SA_Param.NAME);
		SA_Param saParam = (SA_Param) gui.getSelectedIM();
		PeriodParam periodParam = saParam.getPeriodParam();
		gui.addIMTChangeListener(this);

		assertEquals("Event stack should be empty to start", 0, eventStack.size());

		gui.setSelectedIMT(gui.getSelectedIMT());

		assertEquals("Should not fire event when IMT set to itself", 0, eventStack.size());

		gui.setSelectedIMT(MMI_Param.NAME);

		IMTChangeEvent event;
		assertEquals("Should fire 1 event when IMT changed", 1, eventStack.size());
		event = eventStack.pop();
		assertEquals("IMT change event new val is wrong", MMI_Param.NAME , event.getNewIMT().getName());

		periodParam.setValue(0.1);
		assertEquals("Should not fire event when SA period param change, but IMT is MMI", 0, eventStack.size());

		gui.setSelectedIMT(SA_Param.NAME);
		assertEquals("Should fire 1 event when IMT changed", 1, eventStack.size());
		event = eventStack.pop();
		assertEquals("IMT change event new val is wrong", SA_Param.NAME , event.getNewIMT().getName());

		periodParam.setValue(1.0);
		assertEquals("Should fire 1 event when IMT is SA and period changed", 1, eventStack.size());
		event = eventStack.pop();

		periodParam.setValue(1.0);
		assertEquals("Should not fire event when IMT is SA and period set to itself", 0, eventStack.size());
	}

	@Test
	public void testIMTSetting() {
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap = 
			new HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>();

		imrMap.put(TectonicRegionType.ACTIVE_SHALLOW,
				imrs.get(ListUtils.getIndexByName(imrs, CB_2008_AttenRel.NAME)));
		imrMap.put(TectonicRegionType.STABLE_SHALLOW,
				imrs.get(ListUtils.getIndexByName(imrs, CY_2008_AttenRel.NAME)));

		try {
			testSetIMT(PGV_Param.NAME, -1, imrMap);
		} catch (Exception e) {
			fail("Could not set IMT of '"+PGV_Param.NAME+"' in IMRs");
		}

		imrMap.put(TectonicRegionType.SUBDUCTION_INTERFACE,
				imrs.get(ListUtils.getIndexByName(imrs, ZhaoEtAl_2006_AttenRel.NAME)));
		imrMap.put(TectonicRegionType.SUBDUCTION_SLAB,
				imrs.get(ListUtils.getIndexByName(imrs, ZhaoEtAl_2006_AttenRel.NAME)));

		try {
			testSetIMT(SA_Param.NAME, 0.1, imrMap);
		} catch (Exception e) {
			fail("Could not set IMT of '"+SA_Param.NAME+"' in IMRs");
		}
		try {
			testSetIMT(PGA_Param.NAME, -1, imrMap);
		} catch (Exception e) {
			fail("Could not set IMT of '"+PGA_Param.NAME+"' in IMRs");
		}
		
		try {
			testSetIMT(MMI_Param.NAME, -1, imrMap);
			fail("Setting IMT of '"+MMI_Param.NAME+"' in IMRs should fail if it's not supported");
		} catch (Exception e) {}
	}
	
	private void setIMTinGUI(String imtName, double period) {
		gui.setSelectedIMT(imtName);
		if (imtName.equals(SA_Param.NAME))
			gui.getSelectedIM().getIndependentParameter(PeriodParam.NAME).setValue(period);
	}

	private void testSetIMT(String imtName, double period,
			HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap) {
		setIMTinGUI(imtName, period);
		gui.setIMTinIMRs(imrMap);

		for (ScalarIntensityMeasureRelationshipAPI imr : imrMap.values()) {
			testIMTSetCorrectly(imtName, period, imr);
		}
	}
	
	private void testIMTSetCorrectly(String imtName, double period, ScalarIntensityMeasureRelationshipAPI imr) {
		assertEquals("IMT not set properly!", imtName, imr.getIntensityMeasure().getName());
		if (period >= 0) {
			double myPeriod = (Double)((DependentParameterAPI<Double>)imr.getIntensityMeasure())
			.getIndependentParameter(PeriodParam.NAME).getValue();
			assertEquals("Period not set properly!", period, myPeriod, 0.0);
		}
	}
	
	@Test
	public void testSingleIMR() {
		ScalarIntensityMeasureRelationshipAPI cb2008 =
			imrs.get(ListUtils.getIndexByName(imrs, CB_2008_AttenRel.NAME));
		
		gui = new IMT_NewGuiBean(cb2008);
		
		ArrayList<String> supportedIMTs = gui.getSupportedIMTs();
		
		for (ParameterAPI<?> imtParam : cb2008.getSupportedIntensityMeasuresList()) {
			String imtName = imtParam.getName();
			assertTrue("IMT '" + imtName + "' should be in list!",
					supportedIMTs.contains(imtName));
		}
		
		gui.setIMR(cb2008);
		
		String imtName;
		double period;
		
		imtName = PGA_Param.NAME;
		period = -1;
		setIMTinGUI(imtName, period);
		gui.setIMTinIMR(cb2008);
		testIMTSetCorrectly(imtName, period, cb2008);
		
		imtName = SA_Param.NAME;
		period = 0.1;
		setIMTinGUI(imtName, period);
		gui.setIMTinIMR(cb2008);
		testIMTSetCorrectly(imtName, period, cb2008);
		
		imtName = SA_Param.NAME;
		period = 1.0;
		setIMTinGUI(imtName, period);
		gui.setIMTinIMR(cb2008);
		testIMTSetCorrectly(imtName, period, cb2008);
	}

	@Override
	public void imtChange(IMTChangeEvent e) {
		eventStack.push(e);
	}

}
