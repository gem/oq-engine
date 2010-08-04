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

package org.opensha.sha.gui.beans;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.Iterator;

import javax.swing.JEditorPane;
import javax.swing.JPanel;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;

/**
 * Time span gui.
 * 
 * @version $Id: TimeSpanGuiBean.java 5941 2009-10-12 20:38:15Z pmpowers $
 */

public class TimeSpanGuiBean extends JPanel {

	public final static String TIMESPAN_EDITOR_TITLE = "Set Time Span";
	private TimeSpan timeSpan;

	private ParameterListEditor editor;
	private ParameterList parameterList;
	private JEditorPane timespanEditor = new JEditorPane();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	/**
	 * default constructor
	 */
	public TimeSpanGuiBean() {
		parameterList = new ParameterList();
		try {
			jbInit();
		} catch (Exception e) {
			e.printStackTrace();
		}

	}

	/**
	 * Constructor : It accepts the TimeSpan object. This is timeSpan reference
	 * as exists in the ERF.
	 * 
	 * @param timeSpan
	 */
	public TimeSpanGuiBean(TimeSpan timeSpan) {
		this();
		setTimeSpan(timeSpan);
	}

	/**
	 * It accepts the timespan object and shows it based on adjustable params of
	 * this new object
	 * 
	 * @param timeSpan
	 */
	public void setTimeSpan(TimeSpan timeSpan) {
		this.parameterList.clear();
		this.timeSpan = timeSpan;
		if (editor != null)
			this.remove(editor);
		if (timeSpan != null) {
			// get the adjustable params and add them to the list
			Iterator it = timeSpan.getAdjustableParamsIterator();
			while (it.hasNext()) {
				ParameterAPI param = (ParameterAPI) it.next();
				this.parameterList.addParameter(param);
			}
			this.remove(timespanEditor);
			editor = new ParameterListEditor(parameterList);
			editor.setTitle(TIMESPAN_EDITOR_TITLE);
			this.add(editor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
					GridBagConstraints.CENTER, GridBagConstraints.BOTH,
					new Insets(0, 0, 0, 0), 0, 0));
			this.validate();
			this.repaint();
		} else {
			this.add(timespanEditor, new GridBagConstraints(0, 0, 1, 1,
					1.0, 1.0, GridBagConstraints.CENTER,
					GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));

		}
	}

	/**
	 * Return the timeSpan that is shown in gui Bean
	 * 
	 * @return
	 */
	public TimeSpan getTimeSpan() {
		return this.timeSpan;
	}

	private void jbInit() throws Exception {
		String text = "This ERF does not have any Timespan\n";
		this.setLayout(gridBagLayout1);

		timespanEditor.setEditable(false);
		timespanEditor.setText(text);
		//this.setMinimumSize(new Dimension(0, 0));
		this.add(timespanEditor, new GridBagConstraints(0, 0, 1, 1, 1.0,
				1.0, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(4, 4, 4, 4), 0, 0));
	}

	/**
	 * 
	 * @returns the ParameterList
	 */
	public ParameterList getParameterList() {
		return this.parameterList;
	}

	/**
	 * 
	 * @returns the ParameterListEditor
	 */
	public ParameterListEditor getParameterListEditor() {
		return this.editor;
	}

	/**
	 * 
	 * @returns the Visible parameters metadata
	 */
	public String getParameterListMetadataString() {
		if (timeSpan != null) {
			return editor.getVisibleParametersCloned().
				getParameterListMetadataString();
		} else {
			return "No Timespan";
		}
	}

}
