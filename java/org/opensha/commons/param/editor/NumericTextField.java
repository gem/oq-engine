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
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.DecimalFormat;
import java.text.ParseException;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JTextField;
import javax.swing.text.AttributeSet;
import javax.swing.text.BadLocationException;
import javax.swing.text.DefaultCaret;
import javax.swing.text.Document;

import org.opensha.commons.param.editor.document.NumericPlainDocument;


/**
 * <b>Title:</b> NumericTextField<p>
 *
 * <b>Description:</b> Special JTextField that only allows numbers to be typed in. This
 * text field allows for normal number synatx, such as a negative sign, period for decimal point,
 * and commas for deliminating thousands, millions, etc.<p>
 *
 * Note: This is a fairly complex GUI customization that relies upon a NumjericDocument model
 * to determine what types of characters are allowed for a numerical number ( digits, - sign
 * in first location, etc. ) It is beyond the scope of this javadoc to explain it's use
 * fully. It is not necessary for programmers to understand the details. They can just
 * use it like a normal JTextField and just expect it to work. <p>
 *
 * Please consult Swing doucmentation for further details, specifically JTextField and
 * PlainDocument. It is required a programmer understands the Model View Component
 * design architeture to understand the relationship between JTextField and PlainDocument
 * ( and our corresponding NumericTextField and NumericDocument ).<p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public class NumericTextField extends JTextField
    implements NumericPlainDocument.InsertErrorListener {

    /** Class name for debugging. */
    protected final static String C = "NumericTextField";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    public NumericTextField() { this(null, 0, null); }

    public NumericTextField(String text, int columns, DecimalFormat format) {
	    super(null, text, columns);
	    NumericPlainDocument numericDoc = (NumericPlainDocument) this.getDocument();
        if (format != null) numericDoc.setFormat(format);
	    numericDoc.addInsertErrorListener(this);
    }

    public NumericTextField(int columns, DecimalFormat format) {
	    this(null, columns, format);
    }

    public NumericTextField(String text) { this(text, 0, null); }

    public NumericTextField(String text, int columns) {
	    this(text, columns, null);
    }

    public void setFormat(DecimalFormat format) {
	    ((NumericPlainDocument) this.getDocument()).setFormat(format);
    }

    public DecimalFormat getFormat() {
	    return ((NumericPlainDocument) this.getDocument()).getFormat();
    }

    public void formatChanged() { setFormat(getFormat()); }

    public Long getLongValue() throws ParseException {
	    return ((NumericPlainDocument) this.getDocument()).getLongValue();
    }

    public Double getDoubleValue() throws ParseException {
	    return ((NumericPlainDocument) this.getDocument()).getDoubleValue();
    }

    public Number getNumberValue() throws ParseException {
	    return ((NumericPlainDocument) this.getDocument()).getNumberValue();
    }

    public void setValue(Number number) { setText(getFormat().format(number)); }
    public void setValue(long l) { setText(getFormat().format(l)); }
    public void setValue(double d) { setText(getFormat().format(d)); }

    public void normalize() throws ParseException {
	    setText(getFormat().format(getNumberValue()));
    }


    protected final static String S = C + "setText: (): ";
    protected final static String S2 = C + "setText: (): ";

    /**
     * Sets the text of this <code>TextComponent</code>
     * to the specified text.  If the text is <code>null</code>
     * or empty, has the effect of simply deleting the old text.
     * When text has been inserted, the resulting caret location
     * is determined by the implementation of the caret class.
     * <p>
     * This method is thread safe, although most Swing methods
     * are not. Please see
     * <A HREF="http://java.sun.com/products/jfc/swingdoc-archive/threads.html">Threads
     * and Swing</A> for more information. <p>
     *
     * Note: This is where the text field Document model is consulted to see if
     * the text is viable for insertion.
     *
     * @param t the new text to be set
     * @see #getText
     * @see DefaultCaret
     * @beaninfo
     * description: the text of this component
     */
    public void setText(String t) {

        if( D ) System.out.println(S + "Starting: Text = " + t);

        try {
            Document doc = getDocument();
            doc.remove(0, doc.getLength());
            doc.insertString(0, t, null);
        } catch (BadLocationException e) {
            if( D ) System.out.println(S + "ERR: " + e.toString());
	        //UIManager.getLookAndFeel().provideErrorFeedback(NumericTextField.this);
        }
    }



    /**
     * Returns the text contained in this <code>TextComponent</code>.
     * If the underlying document is <code>null</code>,
     * will give a <code>NullPointerException</code>.
     *
     * @return the text
     * @exception NullPointerException if the document is <code>null</code>
     * @see #setText
     */
    public String getText() {

        if( D ) System.out.println(S2 + "Getting Text");

        Document doc = getDocument();
        String txt;
        try {
            txt = doc.getText(0, doc.getLength());
        } catch (BadLocationException e) {
            if( D ) System.out.println(S2 + "ERR: " + e.toString());
            txt = null;
        }
        return txt;
    }

    public void insertFailed(
        NumericPlainDocument doc,
        int offset, String str,
        AttributeSet a
    ) { Toolkit.getDefaultToolkit().beep(); }

    /** Function that must be overidded to return the PlainDocument subclass */
    protected Document createDefaultModel() {
	    return new NumericPlainDocument();
    }

    /** Tester main function that shows how to use this class. */
    public static void main(String[] args) {
        DecimalFormat format = new DecimalFormat("#,###.###");
        format.setGroupingUsed(true);
        format.setGroupingSize(3);
        format.setParseIntegerOnly(false);
        JFrame f = new JFrame("Numeric Text Field Example");
        final NumericTextField tf = new NumericTextField(10, format);
        tf.setValue(123456.789);
        JLabel lbl = new JLabel("Type a number: ");
        f.getContentPane().add(tf, "East");
        f.getContentPane().add(lbl, "West");
        tf.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
            try {
                tf.normalize();
                Long l = tf.getLongValue();
                System.out
                .println("Value is (Long)".concat(String.valueOf(l)));
            } catch (ParseException e1) {
                try {
                Double d = tf.getDoubleValue();
                System.out.println("Value is (Double)"
                               .concat(String.valueOf(d)));
                } catch (ParseException e2) {
                System.out.println(e2);
                }
            }
            }
        });
        f.pack();
        f.setVisible(true);
    }
}
