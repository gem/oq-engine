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

import java.awt.GraphicsConfiguration;
import java.awt.HeadlessException;
import java.util.ArrayList;

import javax.swing.JFrame;

/**
 * <p>Title: DbAdditionFrame.java </p>
 * <p>Description: All the windows which do database addition should extend from
 * this class. This class allows for registering of the listeners so that listeners
 * can perform any additional operation (E.g. - changing the viewing screens)
 * whenever any information is added to the database </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class DbAdditionFrame extends JFrame {

  /**
   *  ArrayList of all the objects who want to listen on addition of information
   *  into the database
   */
  protected ArrayList dbAdditionSuccesslisteners;


  /**
   * Add a listener. Listener should implement DbAdditionListener interface.
   * Listener will receive events whenever a new information is added to the database.
   *
   * @param listener
   */
  public void addDbAdditionSuccessListener( DbAdditionListener listener ) {
    if ( dbAdditionSuccesslisteners == null ) dbAdditionSuccesslisteners = new ArrayList();
    if ( !dbAdditionSuccesslisteners.contains( listener ) ) dbAdditionSuccesslisteners.add( listener );
  }


  /**
   * Remove the listener. Listener will no longer receive any events based on
   * database addition.
   *
   * @param listener
   */
  public  void removeDbAdditionSuccessListener( DbAdditionListener listener ) {
    if ( dbAdditionSuccesslisteners != null && dbAdditionSuccesslisteners.contains( listener ) )
      dbAdditionSuccesslisteners.remove( listener );
  }

  /**
   * Send the event to all the listeners
   * @param value
   */
  protected void sendEventToListeners(Object value) {
    if ( dbAdditionSuccesslisteners==null ||
         dbAdditionSuccesslisteners.size()== 0 ) return;
    // make the event object
    DbAdditionSuccessEvent event = new DbAdditionSuccessEvent(this, value);
    // send to all the listeners
    for(int i=0; i<dbAdditionSuccesslisteners.size(); ++i) {
      DbAdditionListener listener  = (DbAdditionListener)dbAdditionSuccesslisteners.get(i);
      listener.dbAdditionSuccessful(event);
    }
  }

  public DbAdditionFrame() throws HeadlessException {
  }

  public DbAdditionFrame(GraphicsConfiguration gc) {
    super(gc);
  }

  public DbAdditionFrame(String title) throws HeadlessException {
    super(title);
  }

  public DbAdditionFrame(String title, GraphicsConfiguration gc) {
    super(title, gc);
  }

}
