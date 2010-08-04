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

package org.opensha.commons.data.estimate;

/**
 * <p>Title: InvalidParamValException.java </p>
 * <p>Description: This exception is thrown if user tries to set any value in
 * the estimates which violates the constraints of that estimate  </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class InvalidParamValException extends RuntimeException {

  public InvalidParamValException() {
  }

  public InvalidParamValException(String message) {
    super(message);
  }

  public InvalidParamValException(String message, Throwable cause) {
    super(message, cause);
  }

  public InvalidParamValException(Throwable cause) {
    super(cause);
  }
}
