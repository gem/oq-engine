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

package org.opensha.sha.cybershake.gui.util;

import java.awt.BorderLayout;
import java.io.File;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.net.URL;

import javax.swing.JPanel;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.util.FakeParameterListener;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBeanAPI;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.IntensityMeasureRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;


/**
 * This is a class for quickly saving an XML representation of an Attenuation Relationship.
 * 
 * @author kevin
 *
 */
public class AttenRelSaver extends XMLSaver implements IMR_GuiBeanAPI {
	
	private IMR_GuiBean bean;
	private IMT_GuiBean imtBean;
	
	public AttenRelSaver() {
		super();
		bean = createIMR_GUI_Bean();
		ScalarIntensityMeasureRelationshipAPI imr = bean.getSelectedIMR_Instance();
		imtBean = new IMT_GuiBean(imr, imr.getSupportedIntensityMeasuresIterator());
		super.init();
	}
	
	private IMR_GuiBean createIMR_GUI_Bean() {
		return new IMR_GuiBean(this);
	}
	
	public ScalarIntensityMeasureRelationshipAPI getSelectedAttenRel() {
		return bean.getSelectedIMR_Instance();
	}

	@Override
	public JPanel getPanel() {
		JPanel panel = new JPanel(new BorderLayout());
		panel.add(bean, BorderLayout.CENTER);
		panel.add(imtBean, BorderLayout.SOUTH);
		return panel;
	}

	@Override
	public Element getXML(Element root) {
		AttenuationRelationship attenRel = (AttenuationRelationship)bean.getSelectedIMR_Instance();
		attenRel.setIntensityMeasure(imtBean.getIntensityMeasure());
		
		return attenRel.toXMLMetadata(root);
	}
	
	public static AttenuationRelationship LOAD_ATTEN_REL_FROM_FILE(String fileName) throws DocumentException, InvocationTargetException, MalformedURLException {
		return LOAD_ATTEN_REL_FROM_FILE(new File(fileName).toURI().toURL());
	}
	
	public static AttenuationRelationship LOAD_ATTEN_REL_FROM_FILE(URL file) throws DocumentException, InvocationTargetException, MalformedURLException {
		SAXReader reader = new SAXReader();
		
		Document doc = reader.read(file);
		
		Element el = doc.getRootElement().element(IntensityMeasureRelationship.XML_METADATA_NAME);
		
		return (AttenuationRelationship)AttenuationRelationship.fromXMLMetadata(el, new FakeParameterListener());
	}
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		AttenRelSaver saver = new AttenRelSaver();
		saver.setVisible(true);
		
//		CY_2008_AttenRel cy08 = new CY_2008_AttenRel(new FakeParameterListener());
//		
//		cy08.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
//		cy08.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
//		cy08.getParameter(PeriodParam.NAME).setValue(new Double(3.0));
//		
//		
	}

	public void updateIM() {
		
	}

	public void updateSiteParams() {
		
	}

}
