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

package org.opensha.sha.imr.attenRelImpl.gui;

import java.util.HashMap;

import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel;

/**
 *  <b>Title:</b> IMRGuiList<p>
 *
 *  <b>Description:</b> IMRGuiList is just a container list of all the IMR guis
 *  that have been initialized for the IMR tester applet. For each IMR that is
 *  picked an IMR gui is created with the name of the IMR and then stored in the
 *  IMR gui list so that when that same IMR is requested again instead of
 *  recreating it it can just be accessed from this list. This list simply uses
 *  a hash map mapping the IMR gui names to the IMR gui beans.<p>
 *
 * @author     Steven W. Rock
 * @created    February 28, 2002
 * @see        BJF_1997_AttenRel
 * @see        AS_1997_AttenRel
 * @version    1.0
 */
public class AttenuationRelationshipGuiList {

  protected final static String C = "IMRGuiList";
  protected final static boolean D = false;

  /** This is the hash map containing all the instanciated IMRGuiBeans. */
  private HashMap attenRelGuis = new HashMap();

  /** This is the current selected IMR contained within an IMRGuiBean.  */
  private AttenuationRelationshipGuiBean currentGui = null;

  /**
   *  Constructor for the IMRGuiList object
   */
  public AttenuationRelationshipGuiList() {}

  /**
   *  Sets the IMR attribute of the IMRGuiList object.In this function if the
   *  IMR exists and is already the selected one it returns what has been
   *  selected. If it is not the current it looks inside the hash map to see
   *  if it has already been instanciated and returns that then if not it
   *  creates a new IMRGuiBean from the IMR name adds it to the list sets it
   *  as the current and returns it.
   *
   * @param  imName  This is the fully qualified package and class name of
   *      the IMR to implement.
   * @param  applet   The main application that uses this list needed to
   *      create the IMRGuiBean.
   * @return          Description of the Return Value
   */
  public AttenuationRelationshipGuiBean setImr(int index,
                                               AttenuationRelationshipApplet
                                               applet) {

    String imName = (String) AttenuationRelationshipApplet.imNames.get(index);
    if ( (currentGui != null) && (currentGui.getName().equals(imName)))return
        currentGui;
    else if (attenRelGuis.containsKey(imName)) {
      currentGui = (AttenuationRelationshipGuiBean) attenRelGuis.get(imName);
      return currentGui;
    }
    else {
      String className = (String) AttenuationRelationshipApplet.attenRelClasses.
          get(index);
      AttenuationRelationshipGuiBean bean = new AttenuationRelationshipGuiBean(
          className, imName, applet);
      attenRelGuis.put(imName, bean);
      currentGui = bean;
      return currentGui;

    }

  }

}
