package org.opensha.sha.gui.beans;

import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.NoSuchElementException;
import java.util.Stack;

import javax.swing.JCheckBox;
import javax.swing.JComboBox;

import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.util.ListUtils;
import org.opensha.gem.GEM1.scratch.ZhaoEtAl_2006_AttenRel;
import org.opensha.sha.gui.beans.IMR_MultiGuiBean.EnableableCellRenderer;
import org.opensha.sha.gui.infoTools.AttenuationRelationshipsInstance;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CY_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.imr.event.ScalarIMRChangeEvent;
import org.opensha.sha.imr.event.ScalarIMRChangeListener;
import org.opensha.sha.imr.param.IntensityMeasureParams.MMI_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
import org.opensha.sha.util.TRTUtils;
import org.opensha.sha.util.TectonicRegionType;

public class TestIMR_MultiGuiBean implements ScalarIMRChangeListener {
	
	static ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs;
	static ArrayList<TectonicRegionType> demoTRTs;
	static ArrayList<TectonicRegionType> demoTRTsNoSub;
	static ArrayList<TectonicRegionType> demoSingleTRT;
	
	IMR_MultiGuiBean gui;
	
	Stack<ScalarIMRChangeEvent> eventStack = new Stack<ScalarIMRChangeEvent>();

	@BeforeClass
	public static void setUpBeforeClass() {
		AttenuationRelationshipsInstance inst = new AttenuationRelationshipsInstance();
		imrs = inst.createIMRClassInstance(null);
		for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
			imr.setParamDefaults();
		}
		demoTRTs = new ArrayList<TectonicRegionType>();
		demoTRTs.add(TectonicRegionType.ACTIVE_SHALLOW);
		demoTRTs.add(TectonicRegionType.STABLE_SHALLOW);
		demoTRTs.add(TectonicRegionType.SUBDUCTION_INTERFACE);
		demoTRTs.add(TectonicRegionType.SUBDUCTION_SLAB);
		
		demoTRTsNoSub = new ArrayList<TectonicRegionType>();
		demoTRTsNoSub.add(TectonicRegionType.ACTIVE_SHALLOW);
		demoTRTsNoSub.add(TectonicRegionType.STABLE_SHALLOW);
		
		demoSingleTRT = new ArrayList<TectonicRegionType>();
		demoSingleTRT.add(TectonicRegionType.ACTIVE_SHALLOW);
	}
	
	@Before
	public void setUp() throws Exception {
		gui = new IMR_MultiGuiBean(imrs);
	}
	
	@Test
	public void testSetTRT() {
		assertNull("TRTs should be null by default", gui.getTectonicRegions());
		
		assertFalse("without TRTs, multiple IMRs sould be false", gui.isMultipleIMRs());
		
		JCheckBox singleIMRBox = gui.singleIMRBox;
		
		assertFalse("Checkbox should not be showing with no TRTs", gui.isCheckBoxVisible());
		
		HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap = gui.getIMRMap();
		ScalarIntensityMeasureRelationshipAPI singleIMR = gui.getSelectedIMR();
		
		assertEquals("IMRMap should be of size 1 with no TRTs", 1, imrMap.size());
		assertEquals("Single IMR not returning same as first from Map",
				TRTUtils.getFirstIMR(imrMap).getName(), singleIMR.getName());
		
		try {
			gui.setMultipleIMRs(true);
			fail("Setting multiple IMRs with no TRTs should throw an exception.");
		} catch (Exception e1) {}
		
		gui.setTectonicRegions(demoTRTs);
		
		assertTrue("Checkbox should now be showing with TRTs", gui.isCheckBoxVisible());
		assertTrue("Checkbox should be selected by default", singleIMRBox.isSelected());
		
		try {
			gui.getSelectedIMR();
		} catch (Exception e) {
			fail("getSelectedIMR should still work with multiple TRTs, but single IMR selected");
		}
		
		gui.setMultipleIMRs(true);
		assertFalse("Checkbox should now be deselected", singleIMRBox.isSelected());
		
		try {
			gui.getSelectedIMR();
			fail("getSelectedIMR should throw exception when multiple IMRs selected");
		} catch (Exception e) {}
		
		imrMap = gui.getIMRMap();
		
		assertEquals("IMRMap should be of size "+demoTRTs.size()+" with TRTs and multiple selected",
				demoTRTs.size(), imrMap.size());
		
		gui.setMultipleIMRs(false);
		
		try {
			gui.getSelectedIMR();
		} catch (Exception e) {
			fail("getSelectedIMR should still work with multiple TRTs, but single IMR selected");
		}
		
		imrMap = gui.getIMRMap();
		
		assertEquals("IMRMap should be of size 1 with TRTs and single selected", 1, imrMap.size());
		
		gui.setMultipleIMRs(true);
		gui.setMultipleIMRsEnabled(false);
		assertFalse("disabling multi IMRs should deselect as well", gui.isMultipleIMRs());
		gui.setMultipleIMRsEnabled(true);
		gui.setMultipleIMRs(true);
		
		gui.setTectonicRegions(null);
		
		assertFalse("Checkbox should not be showing with no TRTs", gui.isCheckBoxVisible());
		
		gui.setTectonicRegions(demoSingleTRT);
		assertFalse("Checkbox should not be showing with only 1 TRT", gui.isCheckBoxVisible());
	}
	
	@Test
	public void testIMRChangeEvents() {
		gui.addIMRChangeListener(this);
		
		assertEquals("Event stack should be empty to start", 0, eventStack.size());
		
		/*		Test IMR changes firing events				*/
		ScalarIntensityMeasureRelationshipAPI prevIMR = gui.getSelectedIMR();
		gui.setSelectedSingleIMR(BA_2008_AttenRel.NAME);
		assertEquals("Changing IMR should fire a single event", 1, eventStack.size());
		ScalarIMRChangeEvent event = eventStack.pop();
		assertEquals("New IMR in event is wrong!", BA_2008_AttenRel.NAME,
				TRTUtils.getFirstIMR(event.getNewIMRs()).getName());
		assertEquals("Old IMR in event is wrong!", prevIMR.getName(),
				TRTUtils.getFirstIMR(event.getOldValue()).getName());
		
		/*		Test TRT changes firing events				*/
		gui.setTectonicRegions(demoTRTs);
		assertEquals("Should not fire event when TRTs added, but not multiple IMRs selected", 0, eventStack.size());
		
		gui.setMultipleIMRs(false);
		assertEquals("Should not fire event setting to single with single already selected", 0, eventStack.size());
		
		gui.setMultipleIMRs(true);
		assertEquals("Should fire event setting to multiple with single selected", 1, eventStack.size());
		event = eventStack.pop();
		assertEquals("Event newIMRMap should be of size "+demoTRTs.size()+" with TRTs and multiple selected",
				demoTRTs.size(), event.getNewIMRs().size());
		assertEquals("Event oldIMRMap should be of size 1 here",
				1, event.getOldValue().size());
		
		gui.setMultipleIMRs(false);
		assertEquals("Should fire event setting to single with multiple selected", 1, eventStack.size());
		event = eventStack.pop();
		assertEquals("Event newIMRMap should be of size "+demoTRTs.size()+" with TRTs and single selected",
				1, event.getNewIMRs().size());
		assertEquals("Event oldIMRMap should be of size "+demoTRTs.size()+" here",
				demoTRTs.size(), event.getOldValue().size());
		
		/*		Test IMT changes firing events				*/
		gui.setIMT((DependentParameterAPI<Double>) gui.getSelectedIMR().getIntensityMeasure());
		assertEquals("Should not fire event setting IMT to current IMT", 0, eventStack.size());
		
		ScalarIntensityMeasureRelationshipAPI shakeMapIMR =
			(ScalarIntensityMeasureRelationshipAPI) ListUtils.getObjectByName(imrs, ShakeMap_2003_AttenRel.NAME);
		shakeMapIMR.setIntensityMeasure(MMI_Param.NAME);
		DependentParameterAPI<Double> mmiIMR = (DependentParameterAPI<Double>) shakeMapIMR.getIntensityMeasure();
		gui.setIMT(mmiIMR);
		assertEquals("Should fire event setting IMT to MMI when IMR doesn't support it", 1, eventStack.size());
		event = eventStack.pop();
		assertTrue("New IMR should support IMT",
				TRTUtils.getFirstIMR(event.getNewIMRs()).isIntensityMeasureSupported(mmiIMR));
		assertFalse("Old IMR should not support IMT",
				TRTUtils.getFirstIMR(event.getOldValue()).isIntensityMeasureSupported(mmiIMR));
		
		// now lets change back to something that they both support
		ScalarIntensityMeasureRelationshipAPI cb2008 =
			(ScalarIntensityMeasureRelationshipAPI) ListUtils.getObjectByName(imrs, CB_2008_AttenRel.NAME);
		cb2008.setIntensityMeasure(PGA_Param.NAME);
		DependentParameterAPI<Double> pgaIMR = (DependentParameterAPI<Double>) cb2008.getIntensityMeasure();
		gui.setIMT(pgaIMR);
		assertEquals("Should not fire event setting IMT to one supported by current IMR", 0, eventStack.size());
		gui.setIMT(null);
		assertEquals("Should not fire event setting IMT to null", 0, eventStack.size());
	}
	
	@Test
	public void testIMRChangeMethods() {
		try {
			gui.setSelectedSingleIMR(null);
			fail("Should throw exception when setSelectedSingleIMR called with null name");
		} catch (NoSuchElementException e) {}
		
		gui.setSelectedSingleIMR(BA_2008_AttenRel.NAME);
		assertEquals("Single IMR not set correctly!", BA_2008_AttenRel.NAME, gui.getSelectedIMR().getName());
		
		ScalarIntensityMeasureRelationshipAPI shakeMapIMR =
			(ScalarIntensityMeasureRelationshipAPI) ListUtils.getObjectByName(imrs, ShakeMap_2003_AttenRel.NAME);
		shakeMapIMR.setIntensityMeasure(PGA_Param.NAME);
		DependentParameterAPI<Double> pgaIMR = (DependentParameterAPI<Double>) shakeMapIMR.getIntensityMeasure();
		shakeMapIMR.setIntensityMeasure(MMI_Param.NAME);
		DependentParameterAPI<Double> mmiIMR = (DependentParameterAPI<Double>) shakeMapIMR.getIntensityMeasure();
		gui.setIMT(mmiIMR);
		
		try {
			gui.setSelectedSingleIMR(BA_2008_AttenRel.NAME);
			fail("Setting single IMR should fail if IMR doesn't support current IMT!");
		} catch (Exception e) {}
		
		gui.setTectonicRegions(demoTRTs);
		
		try {
			gui.setIMR(ShakeMap_2003_AttenRel.NAME, demoTRTs.get(0));
			fail("Should throw exception when setIMR called in single IMR mode");
		} catch (RuntimeException e) {}
		
		gui.setMultipleIMRs(true);
		
		try {
			gui.setIMR(null, demoTRTs.get(0));
			fail("Should throw exception when setIMR called with null name");
		} catch (NoSuchElementException e) {}
		
		try {
			gui.setIMR(null, demoTRTs.get(0));
			fail("Should throw exception when setIMR called with null name");
		} catch (NoSuchElementException e) {}
		
		try {
			gui.setIMR(ShakeMap_2003_AttenRel.NAME, null);
			fail("Should throw exception when setIMR called with null TRT");
		} catch (RuntimeException e) {}
		
		try {
			gui.setIMR(BA_2008_AttenRel.NAME, demoTRTs.get(0));
			fail("Setting IMR should fail if IMR doesn't support current IMT!");
		} catch (Exception e) {}
		
		gui.setIMT(pgaIMR);
		
		gui.setIMR(CY_2008_AttenRel.NAME, demoTRTs.get(0));
		
		assertEquals("Set IMR for TRT 0 didn't work!",
				CY_2008_AttenRel.NAME, gui.getIMRMap().get(demoTRTs.get(0)).getName());
		
		gui.setTectonicRegions(demoTRTsNoSub);
		
		gui.setIMR(CB_2008_AttenRel.NAME, TectonicRegionType.ACTIVE_SHALLOW);
		gui.setIMR(CY_2008_AttenRel.NAME, TectonicRegionType.STABLE_SHALLOW);
		try {
			gui.setIMR(ZhaoEtAl_2006_AttenRel.NAME, TectonicRegionType.SUBDUCTION_INTERFACE);
			fail("setting IMR for a TRT that's not included should throw an exception.");
		} catch (Exception e) {}
	}
	
	@Test
	public void testTRTSupportedIndications() {
		gui.setTectonicRegions(demoTRTs);
		
		EnableableCellRenderer renderer;
		JComboBox chooser;
		
		chooser = gui.getChooser(null);
		assertTrue("Chooser renderer should be an EnableableCellRenderer",
				chooser.getRenderer() instanceof EnableableCellRenderer);
		renderer = (EnableableCellRenderer) chooser.getRenderer();
		assertNull("TRTs supporteds should be null in single mode", renderer.trtSupported);
		
		gui.setMultipleIMRs(true);
		
		for (TectonicRegionType trt : demoTRTs) {
			chooser = gui.getChooser(trt);
			for (int i=0; i<imrs.size(); i++) {
				ScalarIntensityMeasureRelationshipAPI imr = imrs.get(i);
				gui.setIMR(imr.getName(), trt);
				assertTrue("Chooser renderer should be an EnableableCellRenderer",
						chooser.getRenderer() instanceof EnableableCellRenderer);
				renderer = (EnableableCellRenderer) chooser.getRenderer();
				assertTrue("TRT supported not being set correctly",
						renderer.trtSupported.get(i) == imr.isTectonicRegionSupported(trt));
			}
		}
	}
	
	private void setupMultipleDiffIMRs() {
		gui.setTectonicRegions(demoTRTs);
		
		gui.setMultipleIMRs(true);
		
		gui.setIMR(CB_2008_AttenRel.NAME, TectonicRegionType.ACTIVE_SHALLOW);
		gui.setIMR(CY_2008_AttenRel.NAME, TectonicRegionType.STABLE_SHALLOW);
		gui.setIMR(ZhaoEtAl_2006_AttenRel.NAME, TectonicRegionType.SUBDUCTION_INTERFACE);
		gui.setIMR(ZhaoEtAl_2006_AttenRel.NAME, TectonicRegionType.SUBDUCTION_SLAB);
	}
	
	@Test
	public void testMultiParamEdits() {
		setupMultipleDiffIMRs();
		
		gui.showParamEditor(TectonicRegionType.ACTIVE_SHALLOW);
		verifyParamEditor(gui.getParamEdit(), imrs.get(ListUtils.getIndexByName(imrs, CB_2008_AttenRel.NAME)));
		
		gui.showParamEditor(TectonicRegionType.STABLE_SHALLOW);
		verifyParamEditor(gui.getParamEdit(), imrs.get(ListUtils.getIndexByName(imrs, CY_2008_AttenRel.NAME)));
		
		gui.showParamEditor(TectonicRegionType.SUBDUCTION_INTERFACE);
		verifyParamEditor(gui.getParamEdit(), imrs.get(ListUtils.getIndexByName(imrs, ZhaoEtAl_2006_AttenRel.NAME)));
		
		gui.showParamEditor(TectonicRegionType.SUBDUCTION_SLAB);
		verifyParamEditor(gui.getParamEdit(), imrs.get(ListUtils.getIndexByName(imrs, ZhaoEtAl_2006_AttenRel.NAME)));
	}
	
	private void verifyParamEditor(ParameterListEditor paramEdit, ScalarIntensityMeasureRelationshipAPI imr) {
		for (ParameterAPI<?> param : imr.getOtherParamsList()) {
			assertTrue("Param '" + param.getName() + "' from IMR isn't in the param list!",
					paramEdit.getParameterList().containsParameter(param));
		}
		
		for (ParameterAPI<?> param : paramEdit.getParameterList()) {
			assertTrue("Param '" + param.getName() + "' from param list isn't in the IMR!",
					imr.getOtherParamsList().containsParameter(param));
		}
	}
	
	@Test
	public void testMultiIMRSiteParams() {
		setupMultipleDiffIMRs();
		
		Iterator<ParameterAPI<?>> siteParamIt;
		
		for (ScalarIntensityMeasureRelationshipAPI imr : gui.getIMRMap().values()) {
			ListIterator<ParameterAPI<?>> mySiteParamIt = imr.getSiteParamsIterator();
			
			while (mySiteParamIt.hasNext()) {
				ParameterAPI<?> myParam = mySiteParamIt.next();
				siteParamIt = gui.getMultiIMRSiteParamIterator();
				boolean found = false;
				while (siteParamIt.hasNext()) {
					ParameterAPI<?> param = siteParamIt.next();
					if (myParam.getName().equals(param.getName())) {
						found = true;
						break;
					}
				}
				assertTrue("Param '" + myParam.getName() + "' from IMR not in site params iterator!", found);
			}
		}
	}
	
	@Test
	public void testSingleMetadata() {
		checkMetaForIMR(gui.getSelectedIMR(), gui.getIMRMetadataHTML());
	}
	
	@Test
	public void testMultipleMetadata() {
		setupMultipleDiffIMRs();
		
		String meta = gui.getIMRMetadataHTML();
		
		for (ScalarIntensityMeasureRelationshipAPI imr : gui.getIMRMap().values())
			checkMetaForIMR(imr, meta);
		
		for (TectonicRegionType trt : demoTRTs)
			assertTrue("Metadata doesn't contain TRT: " + trt.toString(), meta.contains(trt.toString()));
	}
	
	private void checkMetaForIMR(ScalarIntensityMeasureRelationshipAPI imr, String meta) {
		assertTrue("Metadata doesn't contain IMR name!", meta.contains(imr.getName()));
		
		for (ParameterAPI<?> param : imr.getOtherParamsList()) {
			if (param.getName().equals(SigmaTruncLevelParam.NAME))
				continue;
			if (param.getName().equals(TectonicRegionTypeParam.NAME))
				continue;
			assertTrue("Metadata doesn't contain IMR param: " + param.getName(), meta.contains(param.getName()));
		}
	}

	@Override
	public void imrChange(ScalarIMRChangeEvent event) {
		eventStack.push(event);
	}

}
