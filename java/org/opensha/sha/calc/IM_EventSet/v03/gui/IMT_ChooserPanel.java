/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.calc.IM_EventSet.v03.gui;

import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;

import javax.swing.JFrame;
import javax.swing.ListModel;

import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

public class IMT_ChooserPanel extends NamesListPanel implements ParameterChangeListener {
	
	private IMT_GuiBean imtGuiBean;
	
	private boolean masterDisable = false;
	
	private ArrayList<ParameterAPI<?>> imts;
	
	public IMT_ChooserPanel() {
		super(null, "Selected IMT(s):");
		imtGuiBean = new IMT_GuiBean(null);
		imts = new ArrayList<ParameterAPI<?>>();
		
		this.setLowerPanel(imtGuiBean);
	}
	
	public void setForceDisableAddButton(boolean disable) {
//		System.out.println("Setting force disable: " + disable);
		masterDisable = disable;
		this.addButton.setEnabled(shouldEnableAddButton());
	}
	
	protected void rebuildList() {
		Object names[] = new Object[imts.size()];
		for (int i=0; i<imts.size(); i++) {
			ParameterAPI<?> imt = imts.get(i);
			names[i] = IM_EventSetOutputWriter.getRegularIMTString(imt) + " (HAZ01 code: " + IM_EventSetOutputWriter.getHAZ01IMTString(imt) + ")";
		}
		namesList.setListData(names);
	}

	@Override
	public void addButton_actionPerformed() {
		ListModel model = namesList.getModel();
		DependentParameterAPI<?> newIMT = (DependentParameterAPI<?>) imtGuiBean.getIntensityMeasure();
		DependentParameterAPI<?> clone = (DependentParameterAPI<?>) newIMT.clone();
		ListIterator<ParameterAPI<?>> it = newIMT.getIndependentParametersIterator();
		while (it.hasNext()) {
			clone.addIndependentParameter((ParameterAPI<?>) it.next().clone());
		}
//		System.out.println("Adding " + clone.getClass().getName());
		imts.add(clone);
		
		rebuildList();
	}

	@Override
	public void removeButton_actionPerformed() {
		ListModel model = namesList.getModel();
		Object names[] = new Object[model.getSize()-1];
		int selected = namesList.getSelectedIndex();
		int cnt = 0;
		for (int i=0; i<model.getSize(); i++) {
			if (selected == i) {
				// remove it
				imts.remove(i);
				continue;
			} else {
				names[cnt] = model.getElementAt(i);
				cnt++;
			}
		}
		namesList.setListData(names);
	}

	@Override
	public boolean shouldEnableAddButton() {
		if (masterDisable)
			return false;
		ParameterAPI<?> imt = imtGuiBean.getIntensityMeasure();
		for (ParameterAPI<?> oldIMT : imts) {
			if (imt.getName().equals(oldIMT.getName())) {
				if (imt.getName().equals(SA_Param.NAME)) {
					DependentParameterAPI<?> oldParam = (DependentParameterAPI<?>) oldIMT;
					DependentParameterAPI<?> newParam = (DependentParameterAPI<?>) imt;
					double oldPeriod = (Double) oldParam.getIndependentParameter(PeriodParam.NAME).getValue();
					double newPeriod = (Double) imtGuiBean.getParameterList().getParameter(PeriodParam.NAME).getValue();
					if (newPeriod == oldPeriod) {
//						System.out.println("Returning a SA false: " + newPeriod + ", " + oldPeriod);
						return false;
					}
				} else {
//					System.out.println("Returning a non SA false");
					return false;
				}
			}
		}
		return true;
	}
	
	public void setIMRs(ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs) {
		// this stes the IMRs in the IMT gui bean (so that only ones that work for all
		// IMRs can be used.
		imtGuiBean.setIM(imrs);
		
		if (imrs == null || imrs.size() == 0) {
//			System.err.println("WARNING: empty IMR array!");
			this.setForceDisableAddButton(true);
			return;
		}
		
		// now we need to see if we have already selected any IMTs that don't work
		// for one of the new IMRs
		ArrayList<Integer> toRemove = new ArrayList<Integer>();
		for (int i=imts.size()-1; i>=0; i--) {
			ParameterAPI<?> imt = imts.get(i);
			for (ScalarIntensityMeasureRelationshipAPI imr : imrs) {
				if (!imr.isIntensityMeasureSupported(imt)) {
					toRemove.add(i);
					break;
				}
			}
		}
		if (toRemove.size() > 0) {
			for (int index : toRemove) {
//				System.out.println("Removing a now-invalid IMT!");
				imts.remove(index);
			}
			rebuildList();
		}
		this.setForceDisableAddButton(imrs.size() == 0);
		imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).addParameterChangeListener(this);
		imtGuiBean.refreshParamEditor();
		imtGuiBean.invalidate();
		imtGuiBean.validate();
		this.validate();
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		JFrame frame = new JFrame();
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setSize(400, 600);
		
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs = new ArrayList<ScalarIntensityMeasureRelationshipAPI>();
		CB_2008_AttenRel cb08 = new CB_2008_AttenRel(null);
		cb08.setParamDefaults();
		imrs.add(cb08);
		
		IMT_ChooserPanel choose = new IMT_ChooserPanel();
		choose.setIMRs(imrs);
		
		frame.setContentPane(choose);
		frame.setVisible(true);
	}

	public void parameterChange(ParameterChangeEvent event) {
//		System.out.println("pchange");
		if (event.getNewValue().equals(SA_Param.NAME)) {
//			System.out.println("Selected SA!");
			ParameterAPI<?> periodParam = imtGuiBean.getParameterList().getParameter(PeriodParam.NAME);
			periodParam.addParameterChangeListener(this);
		}
//		System.out.println("ParamChange!!!!!!!!!");
		addButton.setEnabled(shouldEnableAddButton());
	}
	
	public ArrayList<String> getIMTStrings() {
		ArrayList<String> strings = new ArrayList<String>();
		for (ParameterAPI<?> param : imts) {
			strings.add(IM_EventSetOutputWriter.getRegularIMTString(param));
		}
		return strings;
	}
	
	public void setIMTs(ArrayList<String> imts) {
		for (String imt : imts) {
			StringTokenizer tok = new StringTokenizer(imt.trim());
			String imtName = tok.nextToken();
			
			this.imtGuiBean.getParameterList();
			this.imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME);
			this.imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(imtName);
			if (tok.hasMoreTokens()) {
				Double period = Double.parseDouble(tok.nextToken());
				this.imtGuiBean.getParameterList().getParameter(PeriodParam.NAME).setValue(period);
			}
			this.addButton_actionPerformed();
		}
	}

}
