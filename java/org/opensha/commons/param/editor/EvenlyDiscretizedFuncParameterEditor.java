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

package org.opensha.commons.param.editor;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.awt.event.FocusEvent;
import java.util.StringTokenizer;

import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.param.EvenlyDiscretizedFuncParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;

/**
 * <b>Title:</b> EvenlyDiscretizedFuncParameterEditor<p>
 *
 * <b>Description:</b> Subclass of ParameterEditor for editing EvenlyDiscretizedFuncParameters.
 * The widget consists of fields to specfiy min/max/delta and a JTextArea
 * which allows Y values to be filled in.  <p>
 *
 * @author Vipin Gupta, Nitin Gupta
 * @version 1.0
 */
public class EvenlyDiscretizedFuncParameterEditor extends ParameterEditor
{

    /** Class name for debugging. */
    protected final static String C = "EvenlyDiscretizedFuncParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    //private final static String EDITOR_TITLE = "Evenly Discretized ";

    private final static String  ONE_Y_VAL_MSG = "Each line should have just " +
        "one Y value";
    private final static String Y_VALID_MSG = "Y Values entered must be valid numbers" ;
    private final static String INCORRECT_NUM_Y_VALS = "Number of Y vals should be equal to number of X values";
    protected final static Dimension SCROLLPANE_DIM = new Dimension( 70, 230 );
    /**
     * Paramter List for holding all parameters
     */
    private ParameterList parameterList;

    private EvenlyDiscretizedFuncParameter evenlyDiscrFuncParam;

    /**
     * ParameterListEditor for holding parameters
     */
    private ParameterListEditor editor;

    /**
     * X values text area
     */
    private JTextArea xTextArea;
    // x scroll pane
    private JScrollPane xScrollPane;

    /**
     * Y values text area
     */
    private JTextArea yTextArea;
    // y scroll pane
    private JScrollPane yScrollPane;
    private EvenlyDiscretizedFunc function;
    private String xAxisName = "";
    private String yAxisName = "";
    private  String title ;

    /** No-Arg constructor calls parent constructor */
    public EvenlyDiscretizedFuncParameterEditor() {
      super();
    }

    /**
     * Constructor that sets the parameter that it edits. An
     * Exception is thrown if the model is not an DiscretizedFuncParameter <p>
     */
    public EvenlyDiscretizedFuncParameterEditor(ParameterAPI model) throws
        Exception {

      super(model);

      String S = C + ": Constructor(model): ";
      if (D)
        System.out.println(S + "Starting");

      this.setParameter(model);
      if (D)
        System.out.println(S.concat("Ending"));

    }


    /**
     * Main GUI Initialization point. This block of code is updated by JBuilder
     * when using it's GUI Editor.
     */
    protected void jbInit() throws Exception {
      focusLostProcessing = true;
      this.setLayout(GBL);
    }



    public void setParameter(ParameterAPI param) {

      String S = C + ": Constructor(): ";
      if (D) System.out.println(S + "Starting:");
      if ( (param != null) && ! (param instanceof EvenlyDiscretizedFuncParameter))
        throw new RuntimeException(S +
                                   "Input model parameter must be a EvenlyDiscretizedFuncParameter.");
      setParameterInEditor(param);
      evenlyDiscrFuncParam = (EvenlyDiscretizedFuncParameter)param;
      // make the params editor
      function = (EvenlyDiscretizedFunc)param.getValue();

      xAxisName = "";
      yAxisName = "";
      title = param.getName();
      if(function!=null) {
        if(function.getXAxisName()!=null) xAxisName = function.getXAxisName();
        if(function.getYAxisName()!=null) yAxisName = function.getYAxisName();
      }

      // labels to be displayed on header of text area
      JLabel xLabel = new JLabel(xAxisName);
      JLabel yLabel = new JLabel(yAxisName);


      initParamListAndEditor();
      this.setLayout(GBL);
      add(this.editor, new GridBagConstraints(0, 0, 2, 1, 1.0, 0.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.BOTH,
                                              new Insets(0, 0, 0, 0), 0, 0));

      add(xLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 0.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.NONE,
                                              new Insets(0, 0, 0, 0), 0, 0));
      add(yLabel, new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.NONE,
                                              new Insets(0, 0, 0, 0), 0, 0));

      add(this.xScrollPane, new GridBagConstraints(0, 2, 1, 1, 1.0, 0.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.BOTH,
                                              new Insets(0, 0, 0, 0), 0, 0));
      add(this.yScrollPane, new GridBagConstraints(1, 2, 1, 1, 1.0, 0.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.BOTH,
                                              new Insets(0, 0, 0, 0), 0, 0));


      this.refreshParamEditor();
      // All done
      if (D) System.out.println(S + "Ending:");
    }


    /*
     *
     */
    protected void initParamListAndEditor() {

      // Starting
      String S = C + ": initControlsParamListAndEditor(): ";
      if (D)
        System.out.println(S + "Starting:");
      parameterList = evenlyDiscrFuncParam.getEvenlyDiscretizedParams();
      this.editor = new ParameterListEditor(parameterList);
      editor.setTitle(title);

      xTextArea = new JTextArea();
      xTextArea.setEnabled(false);
      xScrollPane = new JScrollPane(xTextArea);
      xScrollPane.setMinimumSize( SCROLLPANE_DIM );
      xScrollPane.setPreferredSize( SCROLLPANE_DIM );

      yTextArea = new JTextArea();
      yTextArea.addFocusListener(this);
      yScrollPane = new JScrollPane(yTextArea);
      yScrollPane.setMinimumSize( SCROLLPANE_DIM );
      yScrollPane.setPreferredSize( SCROLLPANE_DIM );

    }

    /**
     * It enables/disables the editor according to whether user is allowed to
     * fill in the values.
     */
    public void setEnabled(boolean isEnabled) {
      this.editor.setEnabled(isEnabled);
      this.xTextArea.setEnabled(isEnabled);
      this.yTextArea.setEnabled(isEnabled);

    }


    /**
     * When user clicks in the texstarea to fill up the Y values, fill the X values
     * automatically
     * @param e
     */
    public void focusGained(FocusEvent e)  {
      super.focusGained(e);
      focusLostProcessing = false;
      // check that user has entered min Val
      Double minVal = (Double)parameterList.getParameter(EvenlyDiscretizedFuncParameter.MIN_PARAM_NAME).getValue();
      String isMissing = " is missing";
      if(minVal==null) {
    	this.editor.getParameterEditor(EvenlyDiscretizedFuncParameter.MIN_PARAM_NAME).grabFocus();
        JOptionPane.showMessageDialog(this, EvenlyDiscretizedFuncParameter.MIN_PARAM_NAME+isMissing);
        return;
      }
      double min = minVal.doubleValue();
      // check that user has entered max val
      Double maxVal = (Double)parameterList.getParameter(EvenlyDiscretizedFuncParameter.MAX_PARAM_NAME).getValue();
      if(maxVal==null) {
    	  this.editor.getParameterEditor(EvenlyDiscretizedFuncParameter.MAX_PARAM_NAME).grabFocus();
        JOptionPane.showMessageDialog(this, EvenlyDiscretizedFuncParameter.MAX_PARAM_NAME+isMissing);
        return;
      }
      double max = maxVal.doubleValue();
      //check that user has entered num values
      Integer numVal = (Integer)parameterList.getParameter(EvenlyDiscretizedFuncParameter.NUM_PARAM_NAME).getValue();
      if(numVal==null) {
    	  this.editor.getParameterEditor(EvenlyDiscretizedFuncParameter.NUM_PARAM_NAME).grabFocus();
        JOptionPane.showMessageDialog(this, EvenlyDiscretizedFuncParameter.NUM_PARAM_NAME+isMissing);

        return;
      }
      int num = numVal.intValue();
      double y[] = new double[function.getNum()];
      for(int i=0; i<function.getNum(); ++i)
        y[i] = function.getY(i);
      function.set(min, max, num);
      String xStr = "";
      String yStr = "";
      for(int i=0; i<num; ++i) {
        if(i<y.length) function.set(i,y[i]);
        else function.set(i,0.0);
        xStr = xStr + (float)function.getX(i) + "\n";
        yStr = yStr +  function.getY(i)+" \n";
      }
      xTextArea.setText(xStr);
      yTextArea.setText(yStr);
      focusLostProcessing = true;
    }

    /**
     * returns the Min of the magnitude for the distribution
     * @return
     */
    public double getMin() {

      return ( (Double) parameterList.getParameter(EvenlyDiscretizedFuncParameter.MIN_PARAM_NAME).
              getValue()).doubleValue();
    }

    /**
     * returns the Max of the magnitude for thr distribution
     * @return
     */
    public double getMax() {
      return ( (Double) parameterList.getParameter(EvenlyDiscretizedFuncParameter.MAX_PARAM_NAME).
              getValue()).doubleValue();
    }

    /**
     * returns the Number of magnitudes for the Distribution
     * @return
     */
    public int getNum() {
      return ( (Integer) parameterList.getParameter(EvenlyDiscretizedFuncParameter.NUM_PARAM_NAME).
              getValue()).intValue();
    }


    /**
     * Called when the user clicks on another area of the GUI outside
     * this editor panel. This synchornizes the editor text field
     * value to the internal parameter reference.
     */
    public void focusLost(FocusEvent e) throws ConstraintException {

      String S = C + ": focusLost(): ";
      if(D) System.out.println(S + "Starting");

      super.focusLost(e);

      if(!focusLostProcessing ) return;

      String str = yTextArea.getText();
      StringTokenizer st = new StringTokenizer(str,"\n");
      int yIndex = 0;
      while(st.hasMoreTokens()){
        StringTokenizer st1 = new StringTokenizer(st.nextToken());
        int numVals = st1.countTokens();
        // check that each line in text area just contains 1 value
        if(numVals !=1) {
          JOptionPane.showMessageDialog(this, this.ONE_Y_VAL_MSG);
          return;
        }
        double tempY_Val=0;
        // check that y value is a valid number
        try{
          tempY_Val = Double.parseDouble(st1.nextToken());
          // set the Y value in the function
          function.set(yIndex, tempY_Val);

          ++yIndex;
        }catch(NumberFormatException ex){
          JOptionPane.showMessageDialog(this, Y_VALID_MSG);
          return;
        }catch(DataPoint2DException ex) {
           JOptionPane.showMessageDialog(this, INCORRECT_NUM_Y_VALS);
           return;
        }
      }

      // check that user has entered correct number of Y values
      if(yIndex!=function.getNum())
        JOptionPane.showMessageDialog(this, INCORRECT_NUM_Y_VALS);
      //refreshParamEditor();
      if(D) System.out.println(S + "Ending");
    }


    /**
     * Called when the parameter has changed independently from
     * the editor, such as with the ParameterWarningListener.
     * This function needs to be called to to update
     * the GUI component ( text field, picklist, etc. ) with
     * the new parameter value.
     */
    public void refreshParamEditor() {
      if(evenlyDiscrFuncParam==null || evenlyDiscrFuncParam.getValue()==null) return;
      EvenlyDiscretizedFunc func = (EvenlyDiscretizedFunc)evenlyDiscrFuncParam.getValue();
      parameterList.getParameter(EvenlyDiscretizedFuncParameter.MIN_PARAM_NAME).setValue(new Double(func.getMinX()));
      parameterList.getParameter(EvenlyDiscretizedFuncParameter.MAX_PARAM_NAME).setValue(new Double(func.getMaxX()));
      parameterList.getParameter(EvenlyDiscretizedFuncParameter.NUM_PARAM_NAME).setValue(new Integer(func.getNum()));
      editor.getParameterEditor(EvenlyDiscretizedFuncParameter.MIN_PARAM_NAME).refreshParamEditor();
      editor.getParameterEditor(EvenlyDiscretizedFuncParameter.MAX_PARAM_NAME).refreshParamEditor();
      editor.getParameterEditor(EvenlyDiscretizedFuncParameter.NUM_PARAM_NAME).refreshParamEditor();

      if ( func != null ) { // show X, Y values from the function
        this.xTextArea.setText("");
        this.yTextArea.setText("");
        int num = func.getNum();
        String xText = "";
        String yText= "";
        for(int i=0; i<num; ++i) {
          xText += (float)func.getX(i)  + "\n";
          yText += func.getY(i)  + "\n";
        }
        xTextArea.setText(xText);
        yTextArea.setText(yText);
      }
      else {
        xTextArea.setText("");
        yTextArea.setText("");
      }
      this.repaint();
    }


  }
