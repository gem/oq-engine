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

import java.text.DecimalFormat;
import java.text.ParseException;
import java.text.ParsePosition;

import javax.swing.text.AbstractDocument;
import javax.swing.text.AttributeSet;
import javax.swing.text.BadLocationException;
import javax.swing.text.PlainDocument;

import org.opensha.commons.param.editor.IntegerTextField;
import org.opensha.commons.param.editor.NumericTextField;

/**
 * <b>Title:</b> NumericPlainDocument<p>
 *
 * <b>Description:</b> Model ( or data) associated with an Numeric Text Field.
 * The insertString() function is called whenever data is being entered
 * into the text field. This is where the text field is checked
 * to make sure only numeric valid charachters are being added.<p>
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
 *      return new NumericPlainDocument();
 * }
 * </code><p>
 *
 * Note: SWR: This class was implemented with java JDK 1.3. In the new
 * java JDK 1.4 there is a much simpler way to do this. Now you can
 * create a Formatter (Decimal, Date, etc. ) and simply pass the formatter
 * to a Standard JTextField. No subclasses to make. <p>
 *
 * @see NumericTextField
 * @see IntegerPlainDocument
 * @see IntegerTextField
 * @author Steven W. Rock
 * @version 1.0
 */


public class NumericPlainDocument extends PlainDocument
{

    /** Class name for debugging. */
    protected final static String C = "NumericPlainDocument";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** Listener to be notified of insert errors, typically the text field */
    protected InsertErrorListener errorListener;

    /** Format of this Decimal. Determines what are valid non-digit characters such as decimal point. */
    protected static DecimalFormat defaultFormat = new DecimalFormat();

    /** Format of this Decimal. Determines what are valid non-digit characters such as decimal point. */
    protected DecimalFormat format;

    /** valid char for decimal point */
    protected char decimalSeparator;

    /** valid char for thousands seperator */
    protected char groupingSeparator;

    protected String positivePrefix;
    protected int positivePrefixLen;
    protected String positiveSuffix;
    protected int positiveSuffixLen;

    protected String negativePrefix;
    protected int negativePrefixLen;
    protected String negativeSuffix;
    protected int negativeSuffixLen;

    transient protected ParsePosition parsePos;

    /**
     * Local interface definition that listeners must implement to be notified
     * when isert fails occur due to invalid chars, etc.
     */
    public interface InsertErrorListener{

        public void insertFailed(
            NumericPlainDocument numericplaindocument,
            int i,
            String string,
            AttributeSet attributeset
        );

    }

    /** Default constructor, sets a null format */
    public NumericPlainDocument() {
    	parsePos = new ParsePosition(0);
	    setFormat(null);
    }


    /** Constructor that lets you set the decimal format. */
    public NumericPlainDocument(DecimalFormat format) {
	    parsePos = new ParsePosition(0);
	    setFormat(format);
    }


    /** Constructor that lets you set the content and the decimal format. */
    public NumericPlainDocument(
        AbstractDocument.Content content,
        DecimalFormat format
    ) {
        super(content);
        String S = "NumericPlainDocument: Constructor(content, format): ";

        parsePos = new ParsePosition(0);
        setFormat(format);

        try { format.parseObject(content.getString(0, content.length()), parsePos); }
        catch (Exception e) {
            throw new IllegalArgumentException(S + "Initial context not a valid number" );
        }

        if (parsePos.getIndex() != content.length() - 1)
            throw new IllegalArgumentException(S + "Initial context not a valid number");
    }


    /**
     * Returns the Deciaml format. Decimal strings can have different format, which
     * in effect determines what are the valid characters for thousands
     * seperator char, decimal char, etc.
     */
    public DecimalFormat getFormat() { return format; }

    /**
     * Sets the Deciaml format. Decimal strings can have different format, which
     * in effect determines what are the valid characters for thousands
     * seperator char, decimal char, etc.
     */
    public void setFormat(DecimalFormat fmt) {
        format = fmt != null ? fmt : (DecimalFormat) defaultFormat.clone();

        decimalSeparator = format.getDecimalFormatSymbols().getDecimalSeparator();

        groupingSeparator = format.getDecimalFormatSymbols().getGroupingSeparator();

        positivePrefix = format.getPositivePrefix();
        positivePrefixLen = positivePrefix.length();
        positiveSuffix = format.getPositiveSuffix();
        positiveSuffixLen = positiveSuffix.length();

        negativePrefix = format.getNegativePrefix();
        negativePrefixLen = negativePrefix.length();
        negativeSuffix = format.getNegativeSuffix();
        negativeSuffixLen = negativeSuffix.length();
    }


    /**
     * Helper function that converts the String representation model data
     * into a Number, the superclass of a Double.
     */
    public Number getNumberValue() throws ParseException {

        String S = "NumericPlainDocument: getNumberValue(): ";
        try {

            String context = this.getText(0, this.getLength());
            parsePos.setIndex(0);
            Number result = format.parse(context, parsePos);

            if (parsePos.getIndex() != this.getLength())
            throw new ParseException(S + "Not a valid number: " + context, 0);

            return result;
        }
        catch (BadLocationException e) {
            throw new ParseException(S + "Not a valid number: ", 0);
        }

    }

    /**
     * Helper function that converts the String
     * representation model data into an Long.
     */
    public Long getLongValue() throws ParseException {

        Number result = getNumberValue();
        if (result instanceof Long == false) {
            String S = "NumericPlainDocument: getLongValue(): ";
            throw new ParseException( S + "Not a valid Long: " + result, 0);
        }
        return (Long) result;

    }

    /**
     * Helper function that converts the String representation model data into
     * an Double, i.e. what the model represents
     */
    public Double getDoubleValue() throws ParseException {

        Number result = getNumberValue();
        if (result instanceof Double == false) {
            String S = "NumericPlainDocument: getDoubleValue(): ";
            throw new ParseException(S + "Not a valid Double: " + result, 0);
        }
        return (Double) result;
    }


    /**
     * Method called to add data to the text field. Typically used when
     * users type in text, but may be called by back end process if needed.
     * Throws errors if the string is not valid decimal characters.
     */
    public void insertString(int offset, String str, AttributeSet a)
	    throws BadLocationException
    {

        String S = C + "insertString: (): ";
        if( D ) System.out.println(S + "Starting");

        if (str != null && str.length() != 0) {

            AbstractDocument.Content content = this.getContent();
            int length = content.length();
            int originalLength = length;
            parsePos.setIndex(0);

            String targetString = content.getString(0, offset) +
                str + content.getString(offset,length - offset - 1);

            boolean gotPositive = targetString.startsWith(positivePrefix);
            boolean gotNegative = targetString.startsWith(negativePrefix);
            length = targetString.length();

            do {
                if (gotPositive == true || gotNegative == true) {

                    if (gotPositive == true && gotNegative == true) {
                        if (positivePrefixLen > negativePrefixLen) gotNegative = false;
                        else gotPositive = false;
                    }

                    String suffix;
                    int suffixLength;
                    int prefixLength;

                    if (gotPositive == true) {
                        suffix = positiveSuffix;
                        suffixLength = positiveSuffixLen;
                        prefixLength = positivePrefixLen;
                    }
                    else {
                        suffix = negativeSuffix;
                        suffixLength = negativeSuffixLen;
                        prefixLength = negativePrefixLen;
                    }

                    if (length == prefixLength) break;

                    if (targetString.endsWith(suffix) == false) {
                        int i;
                        for (i = suffixLength - 1; i > 0; i--) {
                            if (targetString.regionMatches(length - i, suffix, 0, i)) {
                                targetString = targetString + suffix.substring(i);
                                break;
                            }
                        }
                        if (i == 0) targetString += suffix;
                        length = targetString.length();
                    }
                }

                format.parse(targetString, parsePos);
                int endIndex = parsePos.getIndex();

                if (endIndex != length

                    && (positivePrefixLen <= 0 || endIndex >= positivePrefixLen
                    || length > positivePrefixLen
                    || !targetString.regionMatches(0, positivePrefix, 0,length))

                    && (negativePrefixLen <= 0 || endIndex >= negativePrefixLen
                    || length > negativePrefixLen
                    || !targetString.regionMatches(0, negativePrefix, 0, length)))
                {

                    char lastChar = targetString.charAt(originalLength - 1);
                    int decimalIndex = targetString.indexOf(decimalSeparator);

                   /* if ((!format.isGroupingUsed()
                        || lastChar != groupingSeparator
                        || decimalIndex != -1)
                        && (format.isParseIntegerOnly() != false
                        || lastChar != decimalSeparator
                        || decimalIndex != originalLength - 1))
                    {
                        if (errorListener != null) errorListener.insertFailed(this, offset, str, a);
                        return;
                    }*/
                }
            }

            while ( true == false);

            String context = this.getText(0, this.getLength());
            if( D ) System.out.println(S + "Current context = " + context);
            if( D ) System.out.println(S + "Inserting " + str + " at " + offset);

            super.insertString(offset, str, a);
            context = this.getText(0, this.getLength());

            if( D ) System.out.println(S + "Ending: New context = " + context);


        }
    }



    /** Adds a listener that is notified when insertString() fails because text is not a decimal number */
    public void addInsertErrorListener(InsertErrorListener l) {
        if (errorListener == null) errorListener = l;
        else throw new IllegalArgumentException
                  ("NumericPlainDocument: addInsertErrorListener(): InsertErrorListener already registered");
    }

    /** Removes a listener that was notified when insertString() fails because text is not a decimal number */
    public void removeInsertErrorListener(InsertErrorListener l) {
        if (errorListener == l) errorListener = null;
    }
}
