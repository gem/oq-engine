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

package org.opensha.commons.gui.plot.jfreechart.logTest;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.util.ListIterator;
import java.util.StringTokenizer;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingConstants;

import org.jfree.data.xy.XYDataItem;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;


/**
 * <p>Title:XYDataWindow </p>
 * <p>Description: This class allows the user to enter the XY data</p>
 * @author : Nitin Gupta
 * @version 1.0
 */

public class XYDataWindow extends JFrame {
  private JPanel jPanel1 = new JPanel();
  private JLabel jLabel1 = new JLabel();
  private JScrollPane dataScroll = new JScrollPane();
  private JTextArea xyText = new JTextArea();
  //stores the XY DataSet
  private XYSeries series =null;
  private JButton doneButton = new JButton();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  private BorderLayout borderLayout1 = new BorderLayout();
  private Component component;

  public XYDataWindow(Component parent,XYSeriesCollection functions) {

    component = parent;
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
    series = functions.getSeries(0);
    setXYDefaultValues();
  }
  private void jbInit() throws Exception {
    this.getContentPane().setLayout(borderLayout1);
    jPanel1.setLayout(gridBagLayout1);
    jLabel1.setFont(new java.awt.Font("Lucida Grande", 1, 13));
    jLabel1.setForeground(new Color(80, 80, 133));
    jLabel1.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel1.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel1.setText("Enter XY DataSet");
    jPanel1.setPreferredSize(new Dimension(250, 650));
    dataScroll.setPreferredSize(new Dimension(250, 650));
    doneButton.setForeground(new Color(80, 80, 133));
    doneButton.setText("Done");
    doneButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        doneButton_actionPerformed(e);
      }
    });
    jPanel1.add(dataScroll,  new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 20, 8, 0), -56, -62));
    jPanel1.add(jLabel1,    new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(36, 20, 0, 10), 0, 0));
    jPanel1.add(doneButton,  new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(544, 6, 19, 8), 30, 7));
    dataScroll.getViewport().add(xyText, null);
    xyText.setBackground(new Color(200, 200, 230));
    xyText.setForeground(new Color(80, 80, 133));
    xyText.setLineWrap(false);
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    this.setSize(new Dimension(349, 650));
    setTitle("XY Data Entry Window");
    this.validate();
    this.repaint();
    this.setLocation((int)component.getX()+component.getWidth()/2,(int)component.getY()/2);
  }


  /**
   * initialise the dataSet values with the default X & Y values in the textArea
   */
  private void setXYDefaultValues(){
    String text ="";
    ListIterator it =series.getItems().listIterator();
    while(it.hasNext()){
      XYDataItem  xyData = (XYDataItem)it.next();
      text += xyData.getX().doubleValue()+"  "+xyData.getY().doubleValue() +"\n";
    }
    xyText.setText(text);
  }


  /**
   *
   * @returns the XY Data set that user entered.
   */
  public XYSeries getDataSet() throws NumberFormatException, NullPointerException{
    series = new XYSeries("Random Data");
    try{
      String data = xyText.getText();
      StringTokenizer st = new StringTokenizer(data,"\n");
      while(st.hasMoreTokens()){
        StringTokenizer st1 = new StringTokenizer(st.nextToken());
        series.add(new Double(st1.nextToken()).doubleValue(),new Double(st1.nextToken()).doubleValue());
      }
    }catch(NumberFormatException e){
      throw new RuntimeException("Must enter valid number");
    }catch(NullPointerException ee){
      throw new RuntimeException("Must enter data in X Y format");
    }
    return series;
  }

  public XYSeries getXYDataSet() {
    return (XYSeries)series;
  }


  private void closeWindow(){
    int flag=0;
    try{

      //if the user text area for the X values is empty
      if(xyText.getText().trim().equalsIgnoreCase("")){
        JOptionPane.showMessageDialog(this,"Must enter X values","Invalid Entry",
                                      JOptionPane.OK_OPTION);
        flag=1;
      }
      //sets the X values in the ArbitrarilyDiscretizedFunc
      getDataSet();
    }catch(NumberFormatException ee){
      //if user has not entered a valid number in the textArea
      JOptionPane.showMessageDialog(this,ee.getMessage(),"Invalid Entry",
                                    JOptionPane.OK_OPTION);
      flag=1;
    }catch(RuntimeException eee){
      //if the user has not entered the X values in increasing order
      JOptionPane.showMessageDialog(this,eee.getMessage(),"Invalid Entry",
                                    JOptionPane.OK_OPTION);
      flag=1;
    }
    //if there is no exception occured and user properly entered the X values
    if(flag==0)
      this.dispose();
    else
      return;


  }

  void doneButton_actionPerformed(ActionEvent e) {
    closeWindow();
  }

}
