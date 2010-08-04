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

package org.opensha.refFaultParamDb.gui.event;

import java.util.EventObject;

/**
 * <p>Title: DbAdditionSuccessEvent.java </p>
 * <p>Description: This event is thrown whenenver new information is added
 * to the database using a GUI component. The listeners need to implement
 * the DbAdditionListener interface to listen to these events </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class DbAdditionSuccessEvent extends EventObject {
  public Object value; // VO object of the data inserted into the database

  /**
   * Constructor
   * @param source - component which created this event and sent to listeners
   * @param value -  object which contains values inserted into the database
   */
  public DbAdditionSuccessEvent(Object source, Object value) {
    super(source);
    this.value = value;
  }

  /**
   * Get the value. This object holds the values inserted into the database
   * @return
   */
  public Object getValue() {
    return this.value;
  }

}
