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

package org.opensha.nshmp.param;

import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.param.StringConstraint;

/**
 * <p>Title: EditableStringConstraint </p>
 *
 * <p>Description:  This constraint contains a list of values that user
 * can choose from. It also allows the user to provide his own value.
 * These can typically be presented in a GUI picklist.
 </p>
 *
 * @author Nitin Gupta and Vipin Gupta
 * @version 1.0
 */
public class EditableStringConstraint
extends StringConstraint {

	/** Class name for debugging. */
	protected final static String C = "EditableStringConstraint";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	/** ArrayList list of possible string values, i.e. allowed values. */
	private ArrayList strings = new ArrayList();



	public EditableStringConstraint() {
		super();
	}

	public EditableStringConstraint(ArrayList strings) throws ConstraintException {
		super(strings);
	}


	/** Returns a copy so you can't edit or damage the origial. */
	public Object clone() {

		EditableStringConstraint c1 = new EditableStringConstraint();
		c1.name = name;
		ArrayList v = getAllowedStrings();
		ListIterator it = v.listIterator();
		while (it.hasNext()) {
			String val = (String) it.next();
			c1.addString(val);
		}

		c1.setNullAllowed(nullAllowed);
		c1.editable = true;
		return c1;
	}


}
