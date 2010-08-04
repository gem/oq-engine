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
 * <b>Title:</b> TranslatorAPI<p>
 *
 * <b>Description:</b> Interface framework API for translators. These
 * translators translate values from normal space to the translated
 * space using translate(). Reverse translates back to normal space. <p>
 *
 * Since the translate() is typically a mathmatical function such as log()
 * or sin(), there are many mathmatical errors that can occur. The Math
 * class is used heavily by this package. Any errors Math may throw are
 * caught anc recast into a TranslateException. <p>
 *
 * Note that for reverse to work properly it must be a one-to-one mapping.
 * However there are no constraints programmed into this assumption. It
 * is up to the developer to program reverse any way they desire.<p>
 *
 *
 * Concrete TranslatorAPI classes can be passed into a TranslatedParameter,
 * then the parameter will use this class to translate values when
 * getting and setting values in the parameter. <p>
 *
 * This one instance is used to let users deal with the log of a value in the
 * IMRTesterApplet, but the IMR when it does it's calculation it uses the normal
 * space values. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public interface TranslatorAPI {

    /**
     * Perform the mathmatical operation on the val - such as take the log.
     * This translates the value to the translated space.
     */
    public double translate(double val) throws TranslateException;

    /**
     * Performs the reverse mathmatical function on a val. The value is
     * assumed to be in the translated space. This operation returns it
     * to normal space. For example this function will take a log value
     * and translate it back to a normal value.
     * @throws TranslateException
     */
    public double reverse(double val) throws TranslateException;
}
