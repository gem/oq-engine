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
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.BorderFactory;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import org.opensha.commons.param.editor.IntegerTextField;

/**
 * <b>Title:</b> SubRectanglePanel<p>
 *
 * <b>Description:</b> Custom GUI Widget that allows you to specify a window
 * into a 2D matrix, i.e. xmin, ymin, xmax, ymax values. This GUI is comprised
 * of 4 text fields and labels corresponding to the 4 indexes for a "window"
 * subset of a matrix. You are also able to set to read only or editable
 * viewing.<p>
 *
 * This widget is currently used by the FaultTesterApplet to let the user
 * redefine the GriddedSubset region into the main GriddedSurface. <p>
 *
 * The widget is initiallized by setting the xmin, xmax, ymin, ymax in
 * the constructor. Once set, the window range cannot go beyond these values.
 * For example, let's say the constructor is (0, 10, 0, 20). Then in th GUI
 * the user can set xmin >=0, xMax <=10, yMin >=0, and yMax <=20. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 * 
 * TODO deprecate??
 * 
 */

public class SubRectanglePanel extends JPanel{

    int xStart, xEnd, yStart, yEnd;
    int xMin, xMax, yMin, yMax;

    final static GridBagLayout GBL = new GridBagLayout();
    final static Insets zero = new Insets(0,0,0,0);
    final static Color darkBlue = new Color(80,80,133);
    final static Color lightBlue = new Color(200,200,230);
    final static Dimension DIM = new Dimension(60, 18);
    final static Font FONT = new java.awt.Font("Dialog", 1, 11);

    JPanel yMaxPanel = new JPanel();
    JPanel yMinPanel = new JPanel();
    JPanel xMaxPanel = new JPanel();
    JPanel xMinPanel = new JPanel();
    JPanel controlPanel = new JPanel();

    JLabel xMinLabel = new JLabel();
    JTextField xMinTextField = new IntegerTextField();

    JLabel xMaxLabel = new JLabel();
    JTextField xMaxTextField = new IntegerTextField();

    JLabel yMinLabel = new JLabel();
    JTextField yMinTextField = new IntegerTextField();

    JLabel yMaxLabel = new JLabel();
    JTextField yMaxTextField = new IntegerTextField();

   // JButton jButton1 = new JButton();
    JLabel xLabel = new JLabel();
    JLabel yLabel = new JLabel();


    /** Returns the value of the XMin field */
    public int getXMin(){ return (new Integer(xMinTextField.getText())).intValue();}
    /** Returns the value of the XMax field */
    public int getXMax(){return (new Integer(xMaxTextField.getText())).intValue();}
    /** Returns the value of the YMin field */
    public int getYMin(){return (new Integer(yMinTextField.getText())).intValue();}
    /** Returns the value of the YMax field */
    public int getYMax(){return (new Integer(yMaxTextField.getText())).intValue();}

    /**
     * Resets the GUI to the full range the x and y values can be. In the
     * case of it's use for a GriddedSubsetSurface, these x,y max and mins
     * would be set to the full size of the GriddedSurface the
     * GriddedSubsetSurface points to.
     */
    public void setFullRange(int xMin, int xMax, int yMin, int yMax){

        this.xMin = xMin;
        xStart = xMin;
        xMinTextField.setText("" + xMin);
        this.xMax = xMax;
        xEnd = xMax;
        xMaxTextField.setText("" + xMax);

        this.yMin = yMin;
        this.yStart = yMin;
        yMinTextField.setText("" + yMin);

        this.yMax = yMax;
        this.yEnd = yMax;
        yMaxTextField.setText("" + yMax);

        xLabel.setText("X Range (" + xStart + "-" + xEnd + ")");
        yLabel.setText("Y Range (" + yStart + "-" + yEnd + ')');

    }

    /**
     * Constructor that sets the GUI to the full range the x and y
     * values can be. In the case of it's use for a GriddedSubsetSurface,
     * these x,y max and mins would be set to the full size of the
     * GriddedSurface the GriddedSubsetSurface points to.
     */
    public SubRectanglePanel(int xMin, int xMax, int yMin, int yMax) {
        try { jbInit(); }
        catch(Exception e) { e.printStackTrace(); }
        setFullRange(xMin, xMax, yMin, yMax);
    }

    private void jbInit() throws Exception {

        this.setBackground(Color.white);
        this.setLayout(GBL);

        xMinPanel.setBackground(Color.white);
        xMinPanel.setLayout(GBL);

        xMaxPanel.setBackground(Color.white);
        xMaxPanel.setLayout(GBL);

        yMinPanel.setBackground(Color.white);
        yMinPanel.setLayout(GBL);

        yMaxPanel.setBackground(Color.white);
        yMaxPanel.setLayout(GBL);

        xMinLabel.setFont(FONT);
        xMinLabel.setForeground(this.darkBlue);
        xMinLabel.setToolTipText("");
        xMinLabel.setText("X Start:  ");

        xMinTextField.setBorder(BorderFactory.createLoweredBevelBorder());
        xMinTextField.setMinimumSize(DIM);
        xMinTextField.setPreferredSize(DIM);
        xMinTextField.setText("0");
        xMinTextField.setHorizontalAlignment(SwingConstants.TRAILING);


        xMaxLabel.setFont(FONT);
        xMaxLabel.setForeground(this.darkBlue);
        xMaxLabel.setToolTipText("");
        xMaxLabel.setText("X End:    ");

        xMaxTextField.setBorder(BorderFactory.createLoweredBevelBorder());
        xMaxTextField.setMinimumSize(DIM);
        xMaxTextField.setPreferredSize(DIM);
        xMaxTextField.setText("0");
        xMaxTextField.setHorizontalAlignment(SwingConstants.TRAILING);


        yMinLabel.setFont(FONT);
        yMinLabel.setForeground(this.darkBlue);
        yMinLabel.setToolTipText("");
        yMinLabel.setText("Y Start:  ");

        yMinTextField.setBorder(BorderFactory.createLoweredBevelBorder());
        yMinTextField.setMinimumSize(DIM);
        yMinTextField.setPreferredSize(DIM);
        yMinTextField.setText("0");
        yMinTextField.setHorizontalAlignment(SwingConstants.TRAILING);


        yMaxLabel.setFont(FONT);
        yMaxLabel.setForeground(this.darkBlue);
        yMaxLabel.setToolTipText("");
        yMaxLabel.setText("Y End:    ");

        yMaxTextField.setBorder(BorderFactory.createLoweredBevelBorder());
        yMaxTextField.setMinimumSize(DIM);
        yMaxTextField.setPreferredSize(DIM);
        yMaxTextField.setText("0");
        yMaxTextField.setHorizontalAlignment(SwingConstants.TRAILING);


        controlPanel.setBackground(Color.white);
        controlPanel.setBorder(BorderFactory.createEtchedBorder());
        controlPanel.setLayout(GBL);

        /*jButton1.setBackground(Color.white);
        jButton1.setFont(FONT);
        jButton1.setForeground(SystemColor.activeCaption);
        jButton1.setBorder(BorderFactory.createRaisedBevelBorder());
        jButton1.setText("Defaults");
        jButton1.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(ActionEvent e) {
                jButton1_actionPerformed(e);
            }
        });*/


        xLabel.setFont(FONT);
        xLabel.setForeground(this.darkBlue);
        xLabel.setText("X Range (0-100)");

        yLabel.setFont(FONT);
        yLabel.setForeground(this.darkBlue);
        yLabel.setText("Y Range ( 0 - 100 )");


        this.add(xMinPanel,    new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));

        this.add(xMaxPanel,      new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));

        this.add(yMinPanel,      new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));

        this.add(yMaxPanel,      new GridBagConstraints(0, 4, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));


        this.add(controlPanel,  new GridBagConstraints(0, 5, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));
       // controlPanel.add(jButton1,       new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
        //    ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(1, 4, 1, 2), 0, 0));
        controlPanel.add(xLabel,       new GridBagConstraints(1, 2, 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));


        xMinPanel.add(xMinLabel,     new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.BOTH, new Insets(0, 0, 0, 3), 0, 0));
        xMinPanel.add(xMinTextField,    new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.EAST, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 0, 0));

        xMaxPanel.add(xMaxLabel,     new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.BOTH, new Insets(0, 0, 0, 3), 0, 0));
        xMaxPanel.add(xMaxTextField,   new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 0, 0));

        yMinPanel.add(yMinLabel,    new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 3), 0, 0));
        yMinPanel.add(yMinTextField,   new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 0, 0));

        yMaxPanel.add(yMaxLabel,    new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 3), 0, 0));
        yMaxPanel.add(yMaxTextField,  new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 0, 0));
        controlPanel.add(yLabel,   new GridBagConstraints(1, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));


    }

    /*void jButton1_actionPerformed(ActionEvent e) {

        this.xMin = xStart;
        xMinTextField.setText("" + xMin);

        this.xMax = xEnd;
        xMaxTextField.setText("" + xMax);

        this.yMin = yStart;
        yMinTextField.setText("" + yMin);

        this.yMax = yEnd;
        yMaxTextField.setText("" + yMax);

    }*/


    /**
     * flag that indicates the current state of the
     * text fields, editable or view only.
     */
    protected boolean enabled = false;

    /** Returns if the fields are currently editable or not */
    public boolean isEnabled(){ return enabled; }


    /** Sets all text fields editable */
    public void enable(){

        enabled = true;
        xMaxTextField.enable();
        xMinTextField.enable();

        yMaxTextField.enable();
        yMinTextField.enable();

    }

    /** Sets all text fields unditable */
    public void disable(){
        enabled = false;

        xMaxTextField.disable();
        xMinTextField.disable();

        yMaxTextField.disable();
        yMinTextField.disable();

    }

    /** Tester function to see the border in action. Shows usage for this class. */
    public static void main( String[] args ) {
        JFrame frame = new JFrame( "SubRectanglePanel" );
        frame.getContentPane().add( new SubRectanglePanel(20, 50, 10, 70) );
        frame.setBounds( 0, 0, 300, 150 );
        frame.setVisible( true );
    }


}
