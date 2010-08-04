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

package org.opensha.commons.gui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingConstants;

/**
 * <b>Title:</b> NameValueLabel<p>
 *
 * <b>Description:</b> A JPanel that contains two
 * labels, one plain and one bold. This is used to display
 * a key, value pair. For example:<br>
 *
 * Employee: Frank Herbert<p>
 *
 * This JPanel provides a display for fields in a class. Soley
 * for display purposes. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class NameValueLabel extends JPanel{


    GridBagLayout gridBagLayout1 = new GridBagLayout();
    JLabel nameLabel = new JLabel();
    JLabel valueLabel = new JLabel();

    private String keyName;
    private String value;

    public NameValueLabel() {
        try { jbInit(); }
        catch(Exception e) { e.printStackTrace(); }
    }

    public void setForground(Color c){
        //super.setForeground(c);
        nameLabel.setForeground(c);
    }

    public void setLableForground(Color c){
        nameLabel.setForeground(c);
    }

    private void jbInit() throws Exception {
        nameLabel.setFont(new java.awt.Font("Dialog", 1, 11));
        nameLabel.setMaximumSize(new Dimension(100, 16));
        nameLabel.setMinimumSize(new Dimension(100, 16));
        nameLabel.setPreferredSize(new Dimension(100, 16));
        nameLabel.setHorizontalAlignment(SwingConstants.LEFT);
        nameLabel.setText("Name");
        this.setBackground(Color.white);
        this.setLayout(gridBagLayout1);
        valueLabel.setFont(new java.awt.Font("Dialog", 0, 11));
        //valueLabel.setBorder(BorderFactory.createLineBorder(Color.black));
        valueLabel.setHorizontalAlignment(SwingConstants.LEFT);
        valueLabel.setText("N/A");
        this.add(nameLabel,    new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));
        this.add(valueLabel,   new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 0), 0, 0));
    }

    public String getKeyName() { return keyName; }
    public void setKeyName(String keyName) {
        this.keyName = keyName;
        nameLabel.setText(keyName);
    }

    public String getValue() { return value; }
    public void setValue(String value) {
        this.value = value;
        valueLabel.setText(value);
    }


}
