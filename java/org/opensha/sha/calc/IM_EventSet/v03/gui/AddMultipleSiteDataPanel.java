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

import javax.swing.JOptionPane;

import org.opensha.commons.data.siteData.SiteDataValue;

public class AddMultipleSiteDataPanel extends NamesListPanel {
	
	private ArrayList<SiteDataValue<?>> vals;
	private AddSiteDataPanel adder;
	
	public AddMultipleSiteDataPanel() {
		super(null, "Site Data Values:");
		adder = new AddSiteDataPanel();
		
		vals = new ArrayList<SiteDataValue<?>>();
		
		this.setLowerPanel(adder);
	}
	
	public ArrayList<SiteDataValue<?>> getValues() {
		return vals;
	}
	
	public void rebuildList() {
		Object names[] = new String[vals.size()];
		for (int i=0; i<vals.size(); i++) {
			SiteDataValue<?> val = vals.get(i);
			names[i] = SitesPanel.getDataListString(i, val);
		}
		namesList.setListData(names);
	}

	@Override
	public void addButton_actionPerformed() {
		SiteDataValue<?> val;
		try {
			val = adder.getValue();
			vals.add(val);
			rebuildList();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			JOptionPane.showMessageDialog(this, "Error parsing value:\n" + e.getMessage(),
					"Error!", JOptionPane.ERROR_MESSAGE);
		}
	}

	@Override
	public void removeButton_actionPerformed() {
		int index = namesList.getSelectedIndex();
		vals.remove(index);
		rebuildList();
	}

	@Override
	public boolean shouldEnableAddButton() {
		return true;
	}

}
