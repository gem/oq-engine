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

package org.opensha.commons.param.editor;

import java.awt.Toolkit;
import java.text.ParseException;

import javax.swing.JTextField;
import javax.swing.text.AttributeSet;
import javax.swing.text.Document;

import org.opensha.commons.param.editor.document.IntegerPlainDocument;

/**
 * <b>Title:</b> IntegerTextField<p>
 *
 * <b>Description:</b> Special JTextField that only allows integers to be typed in. This
 * text field allows for a negative sign as the first character, only digits thereafter.<p>
 *
 * Note: This is a fairly complex GUI customization that relies upon an IntegerDocument model
 * to determine what types of characters are allowed for a integer number ( digits, - sign
 * in first location, etc. ) It is beyond the scope of this javadoc to explain it's use
 * fully. It is not necessary for programmers to understand the details. They can just
 * use it like a normal JTextField and just expect it to work. <p>
 *
 * Please consult Swing doucmentation for further details, specifically JTextField and
 * PlainDocument. It is required a programmer understands the Model View Component
 * design architeture to understand the relationship between JTextField and PlainDocument
 * ( and our corresponding IntegerTextField and IntegerDocument ).<p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public class IntegerTextField extends JTextField
    implements IntegerPlainDocument.InsertErrorListener
{

    /** Class name for debugging. */
    protected final static String C = "IntegerTextField";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    public IntegerTextField() { this(null, 0); }

    public IntegerTextField(String text) { this(text, 0); }

    public IntegerTextField(String text, int columns) {
        super(null, text, columns);
        IntegerPlainDocument doc = (IntegerPlainDocument) this.getDocument();
        doc.addInsertErrorListener(this);
    }

    public Integer getIntegerValue() throws ParseException {
	    return ((IntegerPlainDocument) this.getDocument()).getIntegerValue();
    }

    public void setValue(Integer integer) { this.setText(integer.toString()); }
    public void setValue(int i) { this.setText("" + i); }

    public void insertFailed(
        IntegerPlainDocument doc,
        int offset, String str,
        AttributeSet a, String reason
    ) { Toolkit.getDefaultToolkit().beep();  }

    protected Document createDefaultModel() { return new IntegerPlainDocument(); }
}
