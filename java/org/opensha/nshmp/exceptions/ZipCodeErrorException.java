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

package org.opensha.nshmp.exceptions;

/**
 * <p>Title: ZipCodeErrorException</p>
 *
 * <p>Description: This exception is thrown when user provide incorrect
 * Zip Code</p>
 * @author  Ned Field, Nitin Gupta and EV.Leyendecker
 * @version 1.0
 */
public class ZipCodeErrorException
    extends Exception {

  /**
   * Constructs a new ZipCodeNotFoundException with null as its detail message.
   * he cause is not initialized, and may subsequently be initialized by a
   * call to Throwable.initCause(java.lang.Throwable).
   */
  public ZipCodeErrorException() {
  }

  /**
   * Constructor with String as the error message
   * Constructs a new ZipCodeNotFoundException with the specified detail message.
   * The  cause is not initialized, and may subsequently be initialized by  a
   * call to Throwable.initCause(java.lang.Throwable)
   * @param errMsg : customized error message describing the error, what caused it
   * and what can user do to avoid it.The detail message is saved for later
   * retrieval by the Throwable.getMessage() method.
   */
  public ZipCodeErrorException(String errMsg) {
    super(errMsg);
  }
}
