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

package org.opensha.commons.util;

import java.io.File;
import java.text.Collator;
import java.util.Comparator;

/**
 * <code>Comparator</code> for filenames that promotes directories and sorts
 * by filename for the current <code>Locale</code>.
 *
 * @author Peter Powers
 * @version $Id: FileNameComparator.java 6514 2010-04-02 17:54:13Z pmpowers $
 */
public class FileNameComparator implements Comparator<File> {
	
	// A Collator for String comparisons
	private Collator c = Collator.getInstance();
	
	@Override
	public int compare(File f1, File f2) {
		if (f1 == f2) return 0;
		
		// promote directories for file-directory pairs
		if (f1.isDirectory() && f2.isFile()) return -1;
		if (f1.isFile() && f2.isDirectory()) return 1;
		
		// use Collator for file-file and dir-dir pairs
		return c.compare(f1.getName(), f2.getName());
	}
}
