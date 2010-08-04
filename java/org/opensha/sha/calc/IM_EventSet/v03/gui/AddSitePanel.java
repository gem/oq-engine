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

import javax.swing.BoxLayout;
import javax.swing.JOptionPane;
import javax.swing.JPanel;

import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;

public class AddSitePanel extends JPanel {
	
	private AddMultipleSiteDataPanel adder;
	
	private DoubleParameter latParam = new DoubleParameter("Latitude", 34.0);
	private DoubleParameter lonParam = new DoubleParameter("Longitude", -118.0);
	
	public AddSitePanel() {
		this.setLayout(new BoxLayout(this, BoxLayout.X_AXIS));
		
		ParameterList paramList = new ParameterList();
		paramList.addParameter(latParam);
		paramList.addParameter(lonParam);
		ParameterListEditor paramEdit = new ParameterListEditor(paramList);
		paramEdit.setTitle("New Site Location");
		
		this.add(paramEdit, true);
		
		adder = new AddMultipleSiteDataPanel();
		this.add(adder);
	}
	
	public Location getSiteLocation() {
		return new Location(latParam.getValue(), lonParam.getValue());
	}
	
	public ArrayList<SiteDataValue<?>> getDataVals() {
		ArrayList<SiteDataValue<?>> vals = adder.getValues();
		return vals;
	}
	
	public static void main(String args[]) {
		JOptionPane.showConfirmDialog(null, new AddSitePanel(), "Add Site", JOptionPane.OK_CANCEL_OPTION);
	}

}
