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

package org.opensha.commons.param.editor.document;

import java.text.ParseException;
import java.text.ParsePosition;

import javax.swing.text.AttributeSet;
import javax.swing.text.BadLocationException;
import javax.swing.text.PlainDocument;

import org.opensha.commons.param.editor.IntegerTextField;
import org.opensha.commons.param.editor.NumericTextField;

/**
 * <b>Title:</b> IntegerPlainDocument<p>
 *
 * <b>Description:</b> Model ( or data ) associated with an Integer Text Field.
 * The insertString() function is called whenever data is being entered into
 * the text field. This is where the text field is checked to make sure only
 * integer valid charachters are being added.<p>
 *
 * This is an extention of the Model View Controller (MVC) design pattern that
 * all Java Swing elements are built upon. For example, the Java class JTextField
 * contains a PlainDocument model that actually contains the text of the
 * JTextField. This class simply replaces the JTextField PlainDocument with
 * this document. Then as a user types in text into the textfield, this class
 * instance is consulted to see if they are valid characters the user is
 * typing. <p>
 *
 * You don't have to know the details on how this class works in order to
 * use it. To make  text field that uses this document model simply extend
 * JTextField and overide the method createDefaultModel() by creating
 * an instance of you subclass of Plain Document.
 *
 * <code>
 * protected Document createDefaultModel() {
 *      return new IntegerPlainDocument();
 * }
 * </code><p>
 *
 * Note: SWR: This class was implemented with java JDK 1.3. In the new
 * java JDK 1.4 there is a much simpler way to do this. Now you can
 * instantiate a Formatter ( Decimal, Date, etc. ) and simply pass the formatter
 * to a Standard JTextField. No subclasses to make. <p>
 *
 * @see NumericTextField
 * @see NumericPlainDocument
 * @see IntegerTextField
 * @author Steven W. Rock
 * @version 1.0
 */


public class IntegerPlainDocument extends PlainDocument{

    /** Class name for debugging. */
    protected final static String C = "IntegerPlainDocument";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** Smallest allowed integer value by JVM. These can be changed to be more restrictive. */
    protected int min = Integer.MIN_VALUE;
    /** Largest allowed integer value by JVM. These can be changed to be more restrictive.  */
    protected int max = Integer.MAX_VALUE;

    transient protected ParsePosition parsePos = new ParsePosition(0);

    /** Listener to be notified of insert errors, typically the text field */
    protected InsertErrorListener errorListener;

    /**
     * Local interface definition that listeners must implement to be notified
     * when isert fails occur due to invalid chars, etc.
     */
    public static interface InsertErrorListener {
	    public void insertFailed(
            IntegerPlainDocument integerplaindocument,
            int i, String string,
            AttributeSet attributeset, String string_0_
        );
    }

    /**
     * Method called to add data to the text field. Typically used when
     * users type in text, but may be called by back end process if needed.
     * Throws errors if the string is not valid integer characters.
     */
    public void insertString(int offset, String str, AttributeSet a)
	    throws BadLocationException
    {

        String originalModel = this.getText(0, this.getLength() );
        if(D) System.out.println("IntegerPlainDocument: insertString(): Old Model = " + (originalModel) );
        if(D) System.out.println("IntegerPlainDocument: insertString(): Old Model Length = " + this.getLength() );
        if(D) System.out.println("IntegerPlainDocument: insertString(): Adding String at offset = " + offset);

        if (str != null) {
            if (this.getLength() == 0 && str.charAt(0) == '-')
                super.insertString(offset, str, a);
            else {
                try {
                    int i = new Integer(str).intValue();

                    if (i >= min && i <= max) super.insertString(offset, str, a);
                    else if (errorListener != null) {
                        String s = "IntegerPlainDocument: insertString(): Integer value " +
                                    i + " > max(" + max + ") or min(" + min + ')';
                        errorListener.insertFailed(this, offset, str, a, s);
                    }
                }
                catch (NumberFormatException e) {
                    if (errorListener != null)
                        errorListener.insertFailed(this, offset, str, a,e.toString());
                }
            }
        }
    }

    /** Adds a listener that is notified when insertString() fails because text is not an integer */
    public void addInsertErrorListener(InsertErrorListener l) {
	    if (errorListener == null) errorListener = l;
	    else throw new IllegalArgumentException (C + "addInsertErrorListenerInsert(): ErrorListener already registered");
    }

    /** Removes a listener that was notified when insertString() fails because text is not an integer */
    public void removeInsertErrorListener(InsertErrorListener l) {
	    if (errorListener == l) errorListener = null;
    }

    /** Helper function that converts the String model data into an Integer, what the model represents */
    public Integer getIntegerValue() throws ParseException {

        String S = "IntegerPlainDocument: getIntegerValue(): ";
	    try {

            String context = this.getText(0, this.getLength());
            parsePos.setIndex(0);

            Integer result = new Integer(context);
            if (parsePos.getIndex() != this.getLength())
                throw new ParseException (S + "Not a valid number: " + context, 0);

            return result;
        }
        catch (BadLocationException e) {
            throw new ParseException(S + "Not a valid number: ", 0);
        }
        catch (NumberFormatException e) {
            throw new ParseException (S + "Model String cannot be converted to an Integer" , 0);
        }
    }
}
