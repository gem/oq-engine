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

package org.opensha.sha.gui.controls;

import java.awt.BorderLayout;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.HashMap;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;

import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.cybershake.db.CybershakeERF;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteInfo2DB;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.cybershake.db.PeakAmplitudesFromDB;
import org.opensha.sha.cybershake.param.CyberShakeERFSelectorParam;
import org.opensha.sha.gui.HazardCurveServerModeApplication;
import org.opensha.sha.gui.beans.Site_GuiBean;

public class CyberShakeSiteSetterControlPanel extends ControlPanel implements
		ParameterChangeListener, ActionListener {
	
	public static final String NAME = "CyberShake Sites";
	
	private DBAccess db;
	private CybershakeSiteInfo2DB csSites;
	private PeakAmplitudesFromDB amps2db;
	private ERF2DB erf2db;
	
	private JPanel mainPanel = new JPanel(new BorderLayout());
	
	private JPanel buttonPanel = new JPanel();
	
	private JButton setButton = new JButton("Set Site");
	private JButton refreshButton = new JButton("Refresh Sites");
	
	private ParameterListEditor listEditor = null;
	private ParameterList paramList;
	
	// ********** PARAMS ************
	
	// show all sites
	private BooleanParameter allSitesParam;
	public static final String ALL_SITES_PARAM_NAME = "Show sites without data in DB?";
	public static final boolean ALL_SITES_PARAM_DEFAULT = false;
	
	// Site selection param
	private StringParameter siteSelectionParam;
	
	// ERF selection param
	private CyberShakeERFSelectorParam erfParam;
	
	private ArrayList<CybershakeSite> sites;
	private ArrayList<String> siteNames;
	
	private Site_GuiBean siteGuiBean;
	
	private HashMap<String, CybershakeSite> siteNameIDMap;
	
	private JFrame frame;
	
	public CyberShakeSiteSetterControlPanel(Site_GuiBean siteGuiBean) {
		super(NAME);
		
		this.siteGuiBean = siteGuiBean;
	}
	
	public void doinit() {
		frame = new JFrame();
		frame.setTitle("Set Site for CyberShake Calculations");
		
		db = Cybershake_OpenSHA_DBApplication.db;
		csSites = new CybershakeSiteInfo2DB(db);
		amps2db = new PeakAmplitudesFromDB(db);
		erf2db = new ERF2DB(db);
		
		sites = this.csSites.getAllSitesFromDB();
		siteNames = new ArrayList<String>();
		for (CybershakeSite site : sites) {
			siteNames.add(site.id + ". " + site.name + " (" + site.short_name + ")");
		}
		
		paramList = new ParameterList();
		
		allSitesParam = new BooleanParameter(ALL_SITES_PARAM_NAME, ALL_SITES_PARAM_DEFAULT);
		allSitesParam.addParameterChangeListener(this);
		
		erfParam = new CyberShakeERFSelectorParam(erf2db.getAllERFs());
		erfParam.addParameterChangeListener(this);
		
		siteSelectionParam = new StringParameter(CyberShakePlotFromDBControlPanel.SITE_SELECTOR_PARAM);
		refreshSites();
		
		paramList.addParameter(allSitesParam);
		paramList.addParameter(siteSelectionParam);
		paramList.addParameter(erfParam);
		
		listEditor = new ParameterListEditor(paramList);
		
		mainPanel.add(listEditor, BorderLayout.CENTER);
		
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.X_AXIS));
		buttonPanel.add(setButton);
		buttonPanel.add(refreshButton);
		setButton.addActionListener(this);
		refreshButton.addActionListener(this);
		
		mainPanel.add(buttonPanel, BorderLayout.SOUTH);
		
		frame.setContentPane(mainPanel);
		frame.setSize(400, 600);
	}
	
	private void refreshSites() {
		sites = this.csSites.getAllSitesFromDB();
		siteNames = new ArrayList<String>();
		siteNameIDMap = new HashMap<String, CybershakeSite>();
		
		boolean all = (Boolean)allSitesParam.getValue();
		
		CybershakeERF erf = null;
		
		if (!all)
			erf = erfParam.getSelectedERF();
		
		for (CybershakeSite site : sites) {
			if (!all) {
				// if we're not showing all of the, skip it if it doesn't have amps
				boolean hasAmps = amps2db.hasAmps(site.id, erf.id);
				if (hasAmps) {
//					System.out.println("Has amps for site: " + site.id + ", erf: " + erf.id);
				} else {
//					System.out.println("No amps for site: " + site.id + ", erf: " + erf.id);
					continue;
				}
			}
			String name = site.id + ". " + site.getFormattedName();
			siteNames.add(name);
			siteNameIDMap.put(name, site);
		}
		
		System.out.println("Num sites: " + siteNames.size());
		
		if (siteNames.size() == 0) {
			siteNames.add("<No sites for specified parameters!>");
			setButton.setEnabled(false);
		} else {
			setButton.setEnabled(true);
		}
		
		siteSelectionParam.setConstraint(new StringConstraint(siteNames));
		siteSelectionParam.setValue(siteNames.get(0));
		if (listEditor != null) {
			listEditor.getParameterEditor(siteSelectionParam.getName()).setParameter(siteSelectionParam);
			listEditor.getParameterEditor(siteSelectionParam.getName()).refreshParamEditor();
			listEditor.refreshParamEditor();
		}
	}
	
	public void parameterChange(ParameterChangeEvent event) {
		if (event.getParameter().getName().equals(allSitesParam.getName())) {
			this.refreshSites();
		} else if (event.getParameter().getName().equals(erfParam.getName())) {
			this.refreshSites();
		}
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == setButton) {
			String name = (String)siteSelectionParam.getValue();
			System.out.println("selected site: " + name);
			CybershakeSite site = siteNameIDMap.get(name);
//			gui.setSite(new Site(new Location(site.lat, site.lon)));
			siteGuiBean.getParameterListEditor().getParameterEditor(Site_GuiBean.LATITUDE).setValue(new Double(site.lat));
			siteGuiBean.getParameterListEditor().getParameterEditor(Site_GuiBean.LONGITUDE).setValue(new Double(site.lon));
			siteGuiBean.getParameterListEditor().refreshParamEditor();
		} else if (e.getSource() == refreshButton) {
			this.refreshSites();
		}
	}

	@Override
	public Window getComponent() {
		return frame;
	}

}
