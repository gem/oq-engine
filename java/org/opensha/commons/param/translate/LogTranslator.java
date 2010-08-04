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

package org.opensha.commons.param.translate;

import org.opensha.commons.exceptions.TranslateException;

/**
 * <b>Title:</b> LogTranslator<p>
 *
 * <b>Description:</b> Translates values into the log space and back.
 * Throws translate errors when trying to take the log of negative
 * or zero values. <p>
 *
 * Implementation of a translation framework. These concrete TranslatorAPI classes
 * can be passed into a TranslatedParameter, then the parameter will use this class
 * to translate values when getting and setting values in the parameter. <p>
 *
 * This one instance is used to let users deal with the log of a value in the
 * IMRTesterApplet, but the IMR when it does it's calculation it uses the normal
 * space values. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class LogTranslator implements TranslatorAPI {

    /** Takes the log of a positive value > 0, else throws TranslateException.
     *  Translates values from normal to log space.
     */
    public double translate(double val)  throws TranslateException{
        if( val <= 0 ) throw new TranslateException("Cannot translate zero or negative values into log space.");
        return Math.log(val);
    }

    /** Takes the inverse log of a number, i.e. Math.exp(val). Translates values from
     *  log space to normal space.
     */
    public double reverse(double val)  throws TranslateException{
        //if( val < 0 ) throw new TranslateException("Cannot reverse log negative values from log space.");
        return Math.exp( val );

    }
}
