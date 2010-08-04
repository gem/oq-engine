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

package org.opensha.sha.calc.hazardMap.old.applet;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;

import javax.swing.JButton;
import javax.swing.JPanel;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.gui.beans.GriddedRegionGUIBean;
import org.opensha.commons.mapping.gmt.GMT_Map;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.mapping.gmt.gui.GMT_MapGuiBean;
import org.opensha.sha.calc.hazardMap.old.servlet.PlotServlet;
import org.opensha.sha.calc.hazardMap.old.servlet.PlotServletAccessor;
import org.opensha.sha.gui.beans.IMLorProbSelectorGuiBean;
import org.opensha.sha.gui.infoTools.ImageViewerWindow;

public class PlotPanel extends JPanel implements ActionListener {
	
	private GMT_MapGuiBean mapBean;
	private IMLorProbSelectorGuiBean imlProbGuiBean;
	private GriddedRegionGUIBean regionBean;
	
	private JPanel leftPanel = new JPanel(new BorderLayout());
	
	private String datasetID;
	
	private JButton plotButton = new JButton("Plot dataset");
	
	private PlotServletAccessor plotAccessor = new PlotServletAccessor();
	
	public PlotPanel() {
		super(new BorderLayout());
		
		this.setMaximumSize(new Dimension(HazardMapApplet.DEFAULT_WIDTH - 50, HazardMapApplet.DEFAULT_HIGHT - 50));
		
		mapBean = new GMT_MapGuiBean();
		mapBean.showRegionParams(false);
		mapBean.getParameterList().getParameter(GMT_MapGenerator.LOG_PLOT_NAME).setValue(new Boolean(false));
		mapBean.getParameterList().getParameter(GMT_MapGenerator.GMT_SMOOTHING_PARAM_NAME).setValue(new Boolean(false));
		mapBean.getParameterList().getParameter(
				GMT_MapGenerator.TOPO_RESOLUTION_PARAM_NAME).setValue(GMT_MapGenerator.TOPO_RESOLUTION_NONE);
		mapBean.getParameterList().getParameter(
				GMT_MapGenerator.COAST_PARAM_NAME).setValue(GMT_MapGenerator.COAST_DRAW);
		mapBean.refreshParamEditor();
		
		imlProbGuiBean = new IMLorProbSelectorGuiBean();
		
		regionBean = new GriddedRegionGUIBean();
		regionBean.setMinimumSize(new Dimension(300, 600));
		
		leftPanel.add(imlProbGuiBean, BorderLayout.CENTER);
		
		plotButton.setEnabled(false);
		plotButton.addActionListener(this);
		JPanel topLeft = new JPanel(new BorderLayout());
		topLeft.add(plotButton, BorderLayout.NORTH);
		topLeft.add(regionBean, BorderLayout.CENTER);
		leftPanel.add(topLeft, BorderLayout.NORTH);
		
		this.add(mapBean, BorderLayout.EAST);
		this.add(leftPanel, BorderLayout.WEST);
	}
	
	public void setRegion(GriddedRegion region) {
		if (region == null)
			return;
		regionBean.setFromGriddedRegion(region);
		regionBean.refreshParamEditor();
		System.out.println("Updated region!");
	}
	
	public void setDatasetID(String datasetID) {
		this.datasetID = datasetID;
		this.plotButton.setEnabled(true);
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == plotButton) {
			mapBean.setRegionParams(regionBean.getMinLat(), regionBean.getMaxLat(),
					regionBean.getMinLon(), regionBean.getMaxLon(), regionBean.getGridSpacing());
			mapBean.refreshParamEditor();
			GMT_Map map = mapBean.getGMTObject().getGMTMapSpecification(null);
			boolean isProbAt_IML = imlProbGuiBean.isProbAt_IML();
			double level = imlProbGuiBean.getIML_Prob();
			String overwrite = PlotServlet.PLOT_OVERWRITE_IF_INCOMPLETE; // hardcoded for now
			
			try {
				String mapURL = plotAccessor.getMap(datasetID, map, isProbAt_IML, level, overwrite);
				
				ImageViewerWindow imgView = new ImageViewerWindow(mapURL + GMT_MapGenerator.DEFAULT_JPG_FILE_NAME,
							"", true);
			} catch (IOException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			} catch (ClassNotFoundException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			}
		}
	}

}
