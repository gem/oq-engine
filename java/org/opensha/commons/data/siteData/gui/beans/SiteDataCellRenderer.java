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

package org.opensha.commons.data.siteData.gui.beans;

import java.awt.Color;
import java.awt.Component;
import java.util.ArrayList;
import java.util.HashMap;

import javax.swing.DefaultListCellRenderer;
import javax.swing.JList;

import org.opensha.commons.data.siteData.SiteDataAPI;

public class SiteDataCellRenderer extends DefaultListCellRenderer {
	
	private ArrayList<String> types;
	private ArrayList<Boolean> enabled;
	private ArrayList<Boolean> applicable;
	
	private static final Color NOT_APPLICABLE_COLOR = Color.GRAY;
	private static final Color DEFAULT_ENABLED_COLOR = Color.WHITE;
	private static final Color DEFAULT_DISABLED_COLOR = Color.LIGHT_GRAY;
	private static final Color SELECTED_COLOR = new Color(100, 100, 255);
	
	public static HashMap<String, Color> TYPE_COLOR_MAP = new HashMap<String, Color>();
	
	static {
		TYPE_COLOR_MAP.put(SiteDataAPI.TYPE_VS30, new Color(255, 200, 200));
		TYPE_COLOR_MAP.put(SiteDataAPI.TYPE_WILLS_CLASS, new Color(200, 255, 200));
		TYPE_COLOR_MAP.put(SiteDataAPI.TYPE_DEPTH_TO_2_5, new Color(200, 200, 255));
		TYPE_COLOR_MAP.put(SiteDataAPI.TYPE_DEPTH_TO_1_0, new Color(255, 195, 150));
		TYPE_COLOR_MAP.put(SiteDataAPI.TYPE_ELEVATION, new Color(255, 255, 115));
		TYPE_COLOR_MAP.put(SiteDataAPI.TYPE_TOPOGRAPHIC_SLOPE, new Color(150, 255, 255));
	}
	
	public SiteDataCellRenderer(ArrayList<String> types, ArrayList<Boolean> enabled, ArrayList<Boolean> applicable) {
		this.types = types;
		this.enabled = enabled;
		this.applicable = applicable;
	}
	
	public SiteDataCellRenderer(int num) {
		this.types = new ArrayList<String>();
		this.enabled = new ArrayList<Boolean>();
		this.applicable = new ArrayList<Boolean>();
		
		for (int i=0; i<num; i++) {
			types.add(null);
			enabled.add(null);
			applicable.add(null);
		}
	}
	
	public Component getListCellRendererComponent(JList list, 
			Object value,
			int index, 
			boolean isSelected,
			boolean cellHasFocus) {

		super.getListCellRendererComponent(list, 
				value, 
				index, 
				isSelected, 
				cellHasFocus);
		
		if (index < this.types.size()) {
			String type = this.types.get(index);
			boolean enabled = this.enabled.get(index);
			boolean applicable = this.applicable.get(index);
			
			
			if (isSelected) {
				setBackground(SELECTED_COLOR);
			} else {
				if (applicable) {
					Color color = TYPE_COLOR_MAP.get(type);
					if (enabled) {
						if (color != null) {
							setBackground(color);
						} else {
							setBackground(DEFAULT_ENABLED_COLOR);
						}
					} else {
						if (color != null) {
							int r = (int)(color.getRed() * 0.75 + 0.5);
							int g = (int)(color.getGreen() * 0.75 + 0.5);
							int b = (int)(color.getBlue() * 0.75 + 0.5);
							setBackground(new Color(r, g, b));
						} else {
							setBackground(DEFAULT_DISABLED_COLOR);
						}
					}
				} else {
					setBackground(NOT_APPLICABLE_COLOR);
				}
			}
		}
		
//		setText(strColor);
//		setBackground(color);
		return this;
	}
	
	public void setType(int index, String type) {
		this.types.set(index, type);
	}
	
	public void setEnabled(int index, boolean enabled) {
		this.enabled.set(index, enabled);
	}
	
	public void setApplicable(int index, boolean applicable) {
		this.applicable.set(index, applicable);
	}

	public void setTypes(ArrayList<String> types) {
		this.types = types;
	}

	public void setEnabled(ArrayList<Boolean> enabled) {
		this.enabled = enabled;
	}

	public void setApplicable(ArrayList<Boolean> applicable) {
		this.applicable = applicable;
	}

}
