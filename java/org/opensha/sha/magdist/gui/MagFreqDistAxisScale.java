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

package org.opensha.sha.magdist.gui;


import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.event.ActionEvent;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

/**
 * <p>Title: MagFreDistAxisScale</p>
 * <p>Description:  This Class pop up window when custom scale is selecetd for the combo box that enables the
 * user to customise the X and Y Axis scale</p>
 *
 * @author : Nitin Gupta   Date: Aug,21,2002
 * @version 1.0
 */

public class MagFreqDistAxisScale extends JFrame{

  private MagFreqDistTesterApplet magFreqDistTesterApplet;
  double xIncrMin;
  double xIncrMax, yIncrMin, yIncrMax, xCumMin, xCumMax, yCumMin, yCumMax,xMoMin;
  double xMoMax,yMoMin, yMoMax;

  private Border border1;
  private TitledBorder titledBorder1;
  JPanel jPanel1 = new JPanel();
  JTextField jTextIncrMaxY = new JTextField();
  JTextField jTextIncrMinY = new JTextField();
  JTextField jTextIncrMaxX = new JTextField();
  JTextField jTextIncrMinX = new JTextField();
  JPanel jPanel3 = new JPanel();
  JPanel jPanel2 = new JPanel();
  JPanel jPanel4 = new JPanel();
  JButton jButtonOk = new JButton();
  JLabel jLabel4 = new JLabel();
  JLabel jLabel3 = new JLabel();
  JLabel jLabel2 = new JLabel();
  JLabel jLabel1 = new JLabel();
  JButton jButtonCancel = new JButton();
  private Border border2;
  private TitledBorder titledBorder2;
  private Border border3;
  private TitledBorder titledBorder3;
  private JLabel jLabel5 = new JLabel();
  private JTextField jTextCumMinX = new JTextField();
  private JTextField jTextCumMaxX = new JTextField();
  private JTextField jTextCumMaxY = new JTextField();
  private JTextField jTextCumMinY = new JTextField();
  private JLabel jLabel6 = new JLabel();
  private JLabel jLabel7 = new JLabel();
  private JLabel jLabel8 = new JLabel();
  private JLabel jLabel9 = new JLabel();
  private JTextField jTextMoMinX = new JTextField();
  private JLabel jLabel10 = new JLabel();
  private JTextField jTextMoMaxX = new JTextField();
  private JLabel jLabel11 = new JLabel();
  private JTextField jTextMoMinY = new JTextField();
  private JLabel jLabel12 = new JLabel();
  private JTextField jTextMoMaxY = new JTextField();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  private GridBagLayout gridBagLayout2 = new GridBagLayout();
  private GridBagLayout gridBagLayout3 = new GridBagLayout();
  private GridBagLayout gridBagLayout4 = new GridBagLayout();
  private BorderLayout borderLayout1 = new BorderLayout();


  public MagFreqDistAxisScale(MagFreqDistTesterApplet magFreqDist,double xIncrMin,
                              double xIncrMax,double yIncrMin,double yIncrMax,double xCumMin,
                              double xCumMax,double yCumMin,double yCumMax,double xMoMin,
                              double xMoMax,double yMoMin,double yMoMax) {
    this.magFreqDistTesterApplet= magFreqDist;
    this.xIncrMin =xIncrMin;
    this.xIncrMax =xIncrMax;
    this.yIncrMax =yIncrMax;
    this.yIncrMin =yIncrMin;
    this.xCumMax = xCumMax;
    this.xCumMin = xCumMin;
    this.yCumMax = yCumMax;
    this.yCumMin = yCumMin;
    this.xMoMax =xMoMax;
    this.xMoMin =xMoMin;
    this.yMoMax =yMoMax;
    this.yMoMin =yMoMin;
    try{
      jbInit();
    }catch(Exception e){
      System.out.println("Error Occured while running range combo box: "+e);
    }
  }
  void jbInit() throws Exception {


    border2 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
    titledBorder2 = new TitledBorder(BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161)),"Moment Rate Graph Scale");
    border3 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
    titledBorder3 = new TitledBorder(border3,"Cum Rate Graph Scale");
    this.getContentPane().setBackground(new Color(200, 200, 230));
    border1 = BorderFactory.createLineBorder(SystemColor.controlText,1);
    titledBorder1 = new TitledBorder(BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161)),"Incr Rate Graph Scale");
    this.getContentPane().setLayout(borderLayout1);
    this.setDefaultCloseOperation(DISPOSE_ON_CLOSE);
    jPanel1.setLayout(gridBagLayout4);
    jPanel3.setLayout(gridBagLayout1);
    jPanel3.setBorder(titledBorder2);
    jPanel3.setBackground(new Color(200, 200, 230));
    jPanel2.setLayout(gridBagLayout2);
    jPanel2.setBackground(new Color(200, 200, 230));
    jPanel2.setBorder(titledBorder3);
    jPanel2.setMinimumSize(new Dimension(297, 102));
    jPanel2.setPreferredSize(new Dimension(297, 102));
    jPanel4.setBackground(new Color(200, 200, 230));
    jPanel4.setBorder(titledBorder1);
    jPanel4.setLayout(gridBagLayout3);
    jButtonOk.setBackground(new Color(200, 200, 230));
    jButtonOk.setForeground(new Color(80, 80, 133));
    jButtonOk.setText("OK");
    jButtonOk.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        jButtonOk_actionPerformed(e);
      }
    });
    this.setResizable(false);
    jLabel4.setText("Max Y:");
    jLabel3.setText("Max X:");
    jLabel2.setText("Min Y:");
    jLabel1.setText("Min X:");
    jButtonCancel.setBackground(new Color(200, 200, 230));
    jButtonCancel.setForeground(new Color(80, 80, 133));
    jButtonCancel.setText("Cancel");
    jButtonCancel.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        jButtonCancel_actionPerformed(e);
      }
    });
    jPanel1.setBackground(new Color(200, 200, 230));
    jLabel5.setText("Min X:");
    jLabel6.setText("Min Y:");
    jLabel7.setText("Max X:");
    jLabel8.setText("Max Y:");
    jLabel9.setText("Min X:");
    jLabel10.setText("Max X:");
    jLabel11.setText("Min Y:");
    jLabel12.setText("Max Y:");
    jTextIncrMinX.setText(""+xIncrMin);
    jTextIncrMaxX.setText(""+xIncrMax);
    jTextCumMinX.setText(""+xCumMin);
    jTextCumMaxX.setText(""+xCumMax);
    jTextMoMinX.setText(""+xMoMin);
    jTextMoMaxX.setText(""+xMoMax);
    jTextIncrMinY.setText(""+yIncrMin);
    jTextIncrMaxY.setText(""+yIncrMax);
    jTextCumMinY.setText(""+yCumMin);
    jTextCumMaxY.setText(""+yCumMax);
    jTextMoMinY.setText(""+yMoMin);
    jTextMoMaxY.setText(""+yMoMax);
    jPanel3.add(jLabel10,    new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-3, 25, 0, 0), 6, 5));
    jPanel3.add(jLabel12,  new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 25, 8, 0), 9, 3));
    jPanel3.add(jTextMoMaxY,  new GridBagConstraints(2, 1, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(10, 0, 8, 12), 72, 4));
    jPanel3.add(jTextMoMinX,          new GridBagConstraints(0, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(-3, 48, 0, 7), 55, 4));
    jPanel3.add(jTextMoMinY,   new GridBagConstraints(0, 1, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(10, 48, 8, 7), 72, 4));
    jPanel3.add(jLabel9, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-3, 8, 0, 68), 18, 6));
    jPanel3.add(jTextMoMaxX,   new GridBagConstraints(2, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(-3, 0, 0, 12), 72, 4));
    jPanel3.add(jLabel11, new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(11, 8, 8, 72), 13, 5));
    jPanel1.add(jButtonOk,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 171, 15, 0), 20, -1));
    jPanel1.add(jButtonCancel,  new GridBagConstraints(1, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(6, 7, 15, 18), 3, -1));
    jPanel2.add(jTextCumMinY, new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(19, 0, 6, 0), 79, 4));
    jPanel2.add(jLabel7,  new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-1, 34, 0, 0), 4, 3));
    jPanel2.add(jTextCumMaxX,    new GridBagConstraints(3, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(-1, 0, 0, 12), 74, 4));
    jPanel2.add(jLabel8,  new GridBagConstraints(2, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(22, 34, 6, 0), 5, 8));
    jPanel2.add(jTextCumMaxY,    new GridBagConstraints(3, 1, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(20, 0, 6, 12), 74, 4));
    jPanel2.add(jLabel5, new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-1, 10, 0, 62), 25, 6));
    jPanel2.add(jTextCumMinX, new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(-1, 0, 0, 0), 79, 4));
    jPanel2.add(jLabel6, new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(21, 10, 6, 0), 4, 3));
    jPanel1.add(jPanel3,  new GridBagConstraints(0, 2, 2, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(6, 15, 0, 18), 5, 0));
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    jPanel1.add(jPanel4,  new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(14, 15, 0, 18), 0, -1));
    jPanel4.add(jTextIncrMinX,  new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(4, 0, 0, 0), 72, 3));
    jPanel4.add(jLabel3,  new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(4, 34, 0, 0), 8, 3));
    jPanel4.add(jTextIncrMaxX,  new GridBagConstraints(3, 0, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(4, 0, 0, 12), 72, 3));
    jPanel4.add(jTextIncrMaxY,  new GridBagConstraints(3, 1, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(13, 0, 13, 12), 72, 3));
    jPanel4.add(jLabel4,  new GridBagConstraints(2, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(18, 34, 13, 0), 6, 1));
    jPanel4.add(jTextIncrMinY,  new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(13, 0, 13, 0), 72, 3));
    jPanel4.add(jLabel2,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(18, 9, 13, 0), 5, 1));
    jPanel4.add(jLabel1,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(4, 9, 0, 0), 9, 8));
    jPanel1.add(jPanel2,  new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(6, 15, 0, 18), 0, 0));

  }

  void jButtonOk_actionPerformed(ActionEvent e) {
   try {
      double xIncrMin=Double.parseDouble(this.jTextIncrMinX.getText());
      double xIncrMax=Double.parseDouble(this.jTextIncrMaxX.getText());

      double xCumMin=Double.parseDouble(this.jTextCumMinX.getText());
      double xCumMax=Double.parseDouble(this.jTextCumMaxX.getText());

      double xMoMin=Double.parseDouble(this.jTextMoMinX.getText());
      double xMoMax=Double.parseDouble(this.jTextMoMaxX.getText());


      if(xIncrMin>=xIncrMax  || xCumMin>=xCumMax  || xMoMin>=xMoMax){
        JOptionPane.showMessageDialog(this,new String("Max X must be greater than Min X"),new String("Check Axis Range"),JOptionPane.ERROR_MESSAGE);
        return;
      }
      else
        this.magFreqDistTesterApplet.setXRange(xIncrMin,xIncrMax,xCumMin,xCumMax,xMoMin,xMoMax);

      double yIncrMin=Double.parseDouble(this.jTextIncrMinY.getText());
      double yIncrMax=Double.parseDouble(this.jTextIncrMaxY.getText());

      double yCumMin=Double.parseDouble(this.jTextCumMinY.getText());
      double yCumMax=Double.parseDouble(this.jTextCumMaxY.getText());

      double yMoMin=Double.parseDouble(this.jTextMoMinY.getText());
      double yMoMax=Double.parseDouble(this.jTextMoMaxY.getText());

      if(yIncrMin>=yIncrMax  || yCumMin>=yCumMax  || yMoMin>=yMoMax){
        JOptionPane.showMessageDialog(this,new String("Max Y must be greater than Min Y"),new String("Check Axis Range"),JOptionPane.ERROR_MESSAGE);
        return;
      }
      else
        this.magFreqDistTesterApplet.setYRange(yIncrMin,yIncrMax,yCumMin,yCumMax,yMoMin,yMoMax);
      this.dispose();
    } catch(Exception ex) {
        System.out.println("Exception:"+ex);
        JOptionPane.showMessageDialog(this,new String("Text Entered must be a valid numerical value"),new String("Check Axis Range"),JOptionPane.ERROR_MESSAGE);
    }
  }

  void jButtonCancel_actionPerformed(ActionEvent e) {
       this.dispose();
  }

}
