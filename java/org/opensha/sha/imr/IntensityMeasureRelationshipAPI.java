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

package org.opensha.sha.imr;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.EqkRupture;

/**
 *  <b>Title:</b> IntensityMeasureRelationshipAPI<br>
 *  <b>Description:</b> This is the interface defined for all
 *  IntensityMeasureRelationship classes.  See the abstract class for more
 *  description.<br>
 *
 * @author     Edward H. Field
 * @created    February 21, 2002
 * @version    1.0
 */

public interface IntensityMeasureRelationshipAPI
    extends NamedObjectAPI, XMLSaveable {

  /**
   *  Returns a reference to the current Site object of the IMR
   *
   * @return    The site object
   */
  public Site getSite();

  /**
   *  Sets the Site object as a reference to that passed in.
   *
   * @param  site  The new site object
   */
  public void setSite(Site site);

  /**
   * This sets the Site, EqkRupture, and perhaps other things from the propEffect 
   * object passed in (implementation details will vary according to efficiency considerations).
   * @param propEffect
   */
  public void setPropagationEffect(PropagationEffect propEffect);

  /**
   * This sets the probability to be used for getting the IML at a user-specified
   * probability.  This value is not what is returned by the getExceedProbability() 
   * method, as the latter is what is computed for a specified given IML. It's 
   * important to understand this distinction.
   *
   * @param prob
   *
   * @throws ParameterException
   */
  public void setExceedProb(double prob) throws ParameterException;

  /**
   *  Returns a reference to the current EqkRupture object in the IMR
   *
   * @return    The EqkRupture object
   */
  public EqkRupture getEqkRupture();

  /**
   *  Sets the EqkRupture object in the IMR as a reference
   *  to the one passed in.
   *
   * @param  EqkRupture  The new probEqkRupture object
   */
  public void setEqkRupture(EqkRupture eqkRupture);

  /**
   *  Returns the "value" object of the currently chosen Intensity-Measure
   *  Parameter.
   *
   * @return    The value field of the currently chosen intensityMeasure
   */
  public Object getIntensityMeasureLevel() throws ParameterException;

  /**
   *  Sets the value of the currently chosen Intensity-Measure Parameter.
   *  This is the value that the probability of exceedance is computed for.
   *
   * @param  iml  The new value for the intensityMeasure Parameter
   */
  public void setIntensityMeasureLevel(Object iml) throws ParameterException;

  /**
   *  Sets the intensityMeasure parameter, not as a  pointer to that passed in,
   *  but by finding and setting the internally held one with the same name, and 
   *  also setting the values of any of its independent parameters to be equal
   *  to the associated values of those passed in.  Note that the IML is not
   *  set (the value of the selected IM is not set as the value of that passed in).
   *  The latter could be changed if anyone so desires.
   *
   * @param  intensityMeasure  The new intensityMeasure Parameter
   */
  public void setIntensityMeasure(ParameterAPI intensityMeasure) throws
      ParameterException;

  /**
   *  This sets the intensityMeasure parameter as that which has the name
   *  passed in; no value (level) is set, nor are any of the IM's independent
   *  parameters set (since it's only given the name).
   *
   * @param  intensityMeasure  The new intensityMeasureParameter name
   */
  public void setIntensityMeasure(String intensityMeasureName) throws
      ParameterException;

  /**
   *  Gets a reference to the currently chosen Intensity-Measure Parameter
   *  from the IMR.
   *
   * @return    The intensityMeasure Parameter
   */
  public ParameterAPI getIntensityMeasure();

  /**
   *  Checks whether the intensity measure passed in is supported (checking
   *  whether the name of that passed in is the same as the name of one of the
   *  supported IMs, but not checking whether the value (IML) of that passed in is
   *  supported (this could be changed is anyone so desires).  The name and value 
   *  of all independent parameters associated with the intensity measure are also checked.
   *
   * @param  intensityMeasure  Description of the Parameter
   * @return                   True if this is a supported IMT
   */
  public boolean isIntensityMeasureSupported(ParameterAPI type);
  
  /**
   * Checks if the Parameter is a supported intensity-Measure (checking
   * only the name).
   * @param intensityMeasure Name of the intensity Measure parameter
   * @return
   */
  public boolean isIntensityMeasureSupported(String intensityMeasure);


  /**
   *  Sets the probEqkRupture, site, and intensityMeasure objects
   *  simultaneously.
   *
   * @param  eqkRupture             The new EqkRupture
   * @param  site                   The new Site
   * @param  intensityMeasure       The new IM
   */
  public void setAll(EqkRupture EqkRupture, Site site, ParameterAPI intensityMeasure);
  

  /**
   * Returns a pointer to a parameter if it exists in one of the parameter lists
   *
   * @param name                  Parameter key for lookup
   * @return                      The found parameter
   * @throws ParameterException   If parameter with that name doesn't exist
   */
  public ParameterAPI getParameter(String name) throws ParameterException;

  /**
   * This sets the defaults for all the parameters.
   */
  public void setParamDefaults();

  /**
   *  This calculates the probability that the intensity-measure level
   *  (the value in the Intensity-Measure Parameter) will be exceeded.
   *  This function does not set or return the value in the exceedProbParam,
   *  as the latter is for for computing the IML at a user-supplied prob.
   *
   * @return    The exceed Probability value
   */
  public double getExceedProbability();

  /**
   *  Returns an iterator over all Site-related parameters.
   *
   * @return    The Site Parameters Iterator
   */
  public ListIterator<ParameterAPI<?>> getSiteParamsIterator();

  /**
   *  Returns an iterator over all other parameters.  Other parameters are those
   *  that the exceedance probability depends upon, but that are not a
   *  supported IMT (or one of their independent parameters) and are not contained
   *  in, or computed from, the site or eqkRutpure objects.  Note that this does not
   *  include the exceedProbParam (which exceedance probability does not depend on).
   *
   * @return    Iterator for otherParameters
   */
  public ListIterator<ParameterAPI<?>> getOtherParamsIterator();
  
  /**
   *  Returns an ParameterList of all other parameters.  Other parameters are those
   *  that the exceedance probability depends upon, but that are not a
   *  supported IMT (or one of their independent parameters) and are not contained
   *  in, or computed from, the site or eqkRutpure objects.  Note that this does not
   *  include the exceedProbParam (which exceedance probability does not depend on).
   *
   * @return    Iterator for otherParameters
   */
  public ParameterList getOtherParamsList();

  /**
   *  Returns an iterator over all earthquake-rupture related parameters.
   *
   * @return    The Earthquake-Rupture Parameters Iterator
   */
  public ListIterator<ParameterAPI<?>> getEqkRuptureParamsIterator();

  /**
   *  Returns the iterator over all Propagation-Effect related parameters
   *  A Propagation-Effect related parameter is any parameter
   *  for which the value can be compute from a Site and eqkRupture object.
   *
   * @return    The Propagation Effect Parameters Iterator
   */
  public ListIterator<ParameterAPI<?>> getPropagationEffectParamsIterator();

  /**
   *  Returns the iterator over all supported Intensity-Measure
   *  Parameters.
   *
   * @return    The Supported Intensity-Measures Iterator
   */
  public ListIterator<ParameterAPI<?>> getSupportedIntensityMeasuresIterator();
  
  /**
   *  Returns a list of all supported Intensity-Measure
   *  Parameters.
   *
   * @return    The Supported Intensity-Measures Iterator
   */
  public ParameterList getSupportedIntensityMeasuresList();
  
  /**
   *  Returns name of the IntensityMeasureRelationship.
   *
   * @return    The name string
   */
  public String getName();
  
  /**
   * Returns a Short Name for the IMR
   * @return String
   */
  public String getShortName();

  
  /**
   * This provides a URL where additional info can be found
   * @throws MalformedURLException if returned URL is not a valid URL.
   */
  public URL getInfoURL() throws MalformedURLException;

  /**
   * This converts the IMR to an XML representation in an Element object
   */

  public Element toXMLMetadata(Element root);

}
