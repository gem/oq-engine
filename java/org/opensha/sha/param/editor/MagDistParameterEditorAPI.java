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

package org.opensha.sha.param.editor;


import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.sha.magdist.SummedMagFreqDist;


/**
 * <p>Title: MagDistParameterEditorAPI</p>
 *
 * <p>Description: Both Mag_FreqDistParameterEditor and MagPDF_ParameterEditor
 * implements this API, thus both can provide their own implementation of the
 * methods.</p>
 *
 * @author Nitin Gupta
 * @since April 14,2006
 * @version 1.0
 */
public interface MagDistParameterEditorAPI {


    /** Returns the parameter that is stored internally that this GUI widget is editing */
    public void setParameter( ParameterAPI model );

    /**
     * Checks whether you want to show the Mag Freq Dist Param Editor as button or a panel
     * This function mostly come in handy if instead of displaying this parameter
     * as the button user wants to show it as the Parameterlist in the panel.
     * @param visible : If it it true, button is visible else not visible
     * By default it is visible
     */
    public void setMagFreqDistParamButtonVisible(boolean visible);

    /**
     * Clones the Mag ParamList and the makes the parameters visible based on the
     * selected Distribution.
     * @return
     */
    public ParameterListEditor createMagFreqDistParameterEditor() ;


    /**
     * Sets the Summed Dist plotted to be false or true based on
     * @param sumDistPlotted boolean
     */
    public void setSummedDistPlotted(boolean sumDistPlotted);

    /**
     * Function that returns the magFreDist Param as a parameterListeditor
     * so that user can display it as the panel in window rather then
     * button.
     * @return
     */
    public ParameterListEditor getMagFreqDistParameterEditor();

    /**
     * Called when the parameter has changed independently from
     * the editor, such as with the ParameterWarningListener.
     * This function needs to be called to to update
     * the GUI component ( text field, picklist, etc. ) with
     * the new parameter value.
     */
    public void refreshParamEditor();

    /**
     *  Controller function. Dispacter function. Based on which Mag Dist was
     *  choosen, and which parameters are set. determines which dependent
     *  variable discretized function to return.
     *
     * @return                          The choosenFunction value
     * @exception  ConstraintException  Description of the Exception
     */
    public void setMagDistFromParams() throws ConstraintException;


    /**
     *  Sets the MagDistParam to be SummedMagFreqDist
     *
     * @return                          The choosenFunction value
     * @exception  ConstraintException  Description of the Exception
     */
    public void setMagDistFromParams(SummedMagFreqDist summedDist,
                                     String metadata) throws ConstraintException;


    /**
     * returns the MagDistName
     * @return
     */
    public String getMagDistName();

    /**
     * returns the Min of the magnitude for the distribution
     * @return
     */
    public double getMin();

    /**
     * returns the Max of the magnitude for thr distribution
     * @return
     */
    public double getMax();

    /**
     * returns the Number of magnitudes for the Distribution
     * @return
     */
    public int getNum();

    /**
     * returns the ParamterList for the MagfreqDistParameter
     * @return
     */
    public ParameterList getParamterList();

    /** Returns each parameter for the MagFreqDist */
    public ParameterAPI getParameter(String name) throws ParameterException;

    /** Sets the parameter that is stored internally for this GUI widget to edit */
    public ParameterAPI getParameter();


    /** returns the parameterlist */
    public ParameterList getParameterList();
  }
