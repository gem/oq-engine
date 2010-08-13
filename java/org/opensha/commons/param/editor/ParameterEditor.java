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

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;

import javax.swing.BorderFactory;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterAPI;



/**
 * <b>Title:</b> ParameterEditor<p>
 *
 * <b>Description:</b> This is the base Editor class that all Parameter
 * GUI Editors extend to inherit the common functionality. This editor
 * extends JPanel that uses a TitledBorder to display the name of the
 * Parameter, and has an addWidget function that all subclasses will
 * extend to add different types of text fields or picklists. <p>
 *
 * All the functionality of the Editors are in this class. The only thing that
 * subclasses have to deal with is setting the specific widget for the
 * subclass, and how to handle key and focus events on this widget. <p>

 * The types of widgets added to edit the parameter value are JTextField,
 * NumericTextField, IntegerTextField, or JComboBox for contrained values. <p>
 *
 * Note: There are many static constants such as Colors, fonts, etc. Subclasses
 * should use these static instances. It will cut down on the number of classes
 * instantiated, helps with performance, and maintains a common look and
 * feel for this parameter framework. Each static field will not be commented,
 * they should be self explainatory. You need to understand java Swing to
 * understand all these constants. See each component's Javadoc for further
 * documentation. <p>
 *
 * @author     Steven W. Rock
 * @created    April 17, 2002
 * @version    1.0
 */
public class ParameterEditor
         extends JPanel
         implements
        ParameterEditorAPI,
        FocusListener,
        KeyListener {
	
	private static final long serialVersionUID = 0x60232F6;

        /** Class name for debugging. */
    protected final static String C = "ParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    /** Default text for text field */
    protected final static String DATA_TEXT = "Enter data here";

    /** Default string for parameter title */
    protected final static String LABEL_TEXT = "This is the Label";
    protected final static String EMPTY = "";

    // static defined colors
    //protected static Color BACK_COLOR = Color.white;
    public static Color FORE_COLOR = new Color( 80, 80, 140 );
    protected static Color STRING_BACK_COLOR = Color.lightGray;

    // dimensions for layout of components
    protected final static Dimension LABEL_DIM = new Dimension( 100, 20 );
    protected final static Dimension LABEL_PANEL_DIM = new Dimension( 120, 20 );
    protected final static Dimension WIGET_PANEL_DIM = new Dimension( 120, 28 );
    protected final static Dimension JCOMBO_DIM = new Dimension( 100, 26 );
    protected final static Dimension JLIST_DIM = new Dimension( 100, 100 );


    // Panel layout manager
    protected final static GridBagLayout GBL = new GridBagLayout();

    // insets used to layout components.
    protected final static Insets ZERO_INSETS = new Insets( 0, 0, 0, 0 );
    protected final static Insets FIVE_INSETS = new Insets( 0, 5, 0, 0 );
    protected final static Insets FIVE_FIVE_INSETS = new Insets( 0, 5, 0, 5 );

    // Default fonts
    protected static Font JCOMBO_FONT = new Font( "SansSerif", 0, 11 );
    public static Font DEFAULT_LABEL_FONT = new Font( "SansSerif", Font.BOLD, 12 );
    public static Font DEFAULT_FONT = new Font( "SansSerif", Font.PLAIN, 11 );

    // Default borders
    //protected final static Border BORDER = new SidesBorder( BACK_COLOR, BACK_COLOR, BACK_COLOR, BACK_COLOR );
    protected final static Border CONST_BORDER = BorderFactory.createLineBorder( Color.blue, 1 );
    protected final static Border FOCUS_BORDER = BorderFactory.createLineBorder( Color.orange, 1 );
    protected final static Border ETCHED = BorderFactory.createEtchedBorder();

    // Constraints for each specific panel
    protected final static GridBagConstraints OUTER_PANEL_GBC = new GridBagConstraints(
            0, 0, 1, 1, 1.0, 1.0, 10, 1, new Insets( 1, 0, 0, 0 ), 0, 0 );

    protected final static GridBagConstraints WIDGET_PANEL_GBC = new GridBagConstraints(
            0, 1, 1, 1, 1.0, 0.0, 10, 2, ZERO_INSETS, 0, 0 );

    protected final static GridBagConstraints WIDGET_GBC = new GridBagConstraints(
            0, 0, 1, 1, 1.0, 0.0, 10, 2, new Insets( 1, 5, 0, 1 ), 0, 0 );

    protected final static GridBagConstraints COMBO_WIDGET_GBC = new GridBagConstraints(
            0, 0, 1, 1, 1.0, 0.0, 10, 2, new Insets( 1, 0, 0, 1 ), 0, 0 );

    // Actually panels all other componets are placed in
    protected JPanel outerPanel = new JPanel();
    protected JPanel labelPanel = new JPanel();
    protected JPanel widgetPanel = new JPanel();
    protected JLabel nameLabel = new JLabel();
    protected boolean focusEnabled = true;
    protected Border border1;

    /** This border displays the name of the parameter. */
    protected TitledBorder titledBorder1;

    /**
     *  This is a VERY IMPORTANT component to understand this framework.
     *  This is the component that all subclasses must overide. Could be a
     *  JTextField, JComboBox, NumericTextField, etc.
     */
    protected JComponent valueEditor = null;

    /** The internal parameter that this Editor is editing */
    protected ParameterAPI model;

    /**
     * Flag whether to catch errors when constraint error thrown. Resets
     * value to last value before setting with new value.
     */
    protected boolean catchConstraint = false;


    /** Flag to indicate that this widget is processing a key typed event */
    protected boolean keyTypeProcessing = false;

    /** Flag to indicate that this widget is processing a focus lost event */
    protected boolean focusLostProcessing = false;


    /** Constructor for the ParameterEditor hat just calls jbinit().  */
    public ParameterEditor() {

      //  String S = C + ": Constructor(): ";
        try { jbInit(); }
        catch ( Exception e ) { e.printStackTrace(); }

    }


    /**
     *  Constructor for the ParameterEditor that set's the parameter
     *  then calls jbInit(). Throws a NullPointerException if the
     *  passed in parameter is null.
     */
    public ParameterEditor( ParameterAPI model ) {

        String S = C + ": Constructor(model): ";
        if ( model == null ) throw new NullPointerException( S + "Input Parameter data cannot be null" );

        try { jbInit(); }
        catch ( Exception e ) { e.printStackTrace(); }
        setParameter( model );

    }

    /**
     *  Needs to be called by subclasses when editable widget field changed.
     *  If the input value is null, checks if the parameter allows nulls, else
     *  returns without an update. If the value is not null, set's the parameter
     *  value. The parameter may throw a constraint exception. If setting the
     *  parameter succeedes a ParameterChangeEvent is created and all
     *  parameter change listeners are notified of the new value.
     *
     * @param  value                    The new value to set in the parameter.
     * @exception  ConstraintException  Thrown if the parameter rejects the new value.
     */
    public void setValue( Object value ) throws ConstraintException {

        String S = C + ": setValue():";
        if(D) System.out.println(S + "Starting");

        if ( ( model != null ) && ( value == null ) ) {
            if( model.isNullAllowed() ){
                try{
                    model.setValue( value );

                }
                catch(ParameterException ee){
                  ee.printStackTrace();

                }
            }
            else return;
        }
        else if ( model != null  ) {

            Object obj = model.getValue();
            if ( D ) System.out.println( S + "Old Value = " + obj.toString() );
            if ( D ) System.out.println( S + "Model's New Value = " + value.toString() );


            if (  ( obj == null )  ||   ( !obj.toString().equals( value.toString() ) )  ) {


                try{
                    model.setValue( value );
                }
                catch(ParameterException ee){
                    ee.printStackTrace();

                }
            }
        }

        if(D) System.out.println(S + "Ending");

    }

    /**
     * Set's the parameter to be edited by this editor.
     * The editor is updated with the name of the parameter as well as the widget
     * component value. It attempts to use the Constraint name ifdifferent from
     * the parameter and present, else uses the parameter name
     * @param model : Parameter
     */
    public void setParameterInEditor(ParameterAPI model){
      String S = C + ": setParameter(): ";
      if ( model == null )
        throw new NullPointerException( S + "Input Parameter data cannot be null" );
      else
        this.model = model;

      //String name = "";
      //name = 
      model.getName();
      //Object value = 
      model.getValue();
    }

    /**
     *  Set's the parameter to be edited by this editor. The editor is
     *  updated with the name of the parameter as well as the widget
     *  component value. It attempts to use the Constraint name if
     *  different from the parameter and present, else uses the
     *  parameter name. This function actually just calls
     *  removeWidget() then addWidget() then setWidgetObject().
     */
    public void setParameter( ParameterAPI model ) {

        setParameterInEditor(model);
        removeWidget();
        addWidget();

        setWidgetObject( model.getName(), model.getValue() );

    }

    /**
     * Set the value of the parameer as a String, regardless of it's true data type .
     * Internally the string is converted to the correct data type if possible.
     * This base class does nothing in this function, i.e. empty function. To be
     * determined by subclasses.
     */
    public void setAsText( String string ) throws IllegalArgumentException { }

    /**
     * VERY IMPORTANT function to understand this framework. This
     * is the function overidden by all subclasses to add different types
     * of editors. The titled border name is also updated. This base class
     * has no editor widget assigned to it so it just updates the
     * titled border parameter name and sets the tooltip.
     */
    protected void setWidgetObject( String name, Object obj ) {
        updateNameLabel( name );
        setNameLabelToolTip( model.getInfo() );
    }

    /**
     * The tooltip for the name label ( titled border ) can add
     * additional informartion about the Parameter. Typically
     * this info is too long to provide in the Parameter name,
     * such as string units, etc.
     */
    protected void setNameLabelToolTip( String str ) {

        if ( ( str != null ) && !( str.equals( EMPTY ) ) ) {
            if( nameLabel != null) nameLabel.setToolTipText( str );
            this.setToolTipText(str);
        }
        else {
            if( nameLabel != null) nameLabel.setToolTipText( null );
            this.setToolTipText(null);
        }
    }
 /** Sets the focusEnabled boolean indicating this is the GUI componet with the current focus */
    public void setFocusEnabled( boolean newFocusEnabled ) { focusEnabled = newFocusEnabled; }

    /**
     * Exposes the underlying value editor
     * @return The JComponent of this Editor class
     */
    public JComponent getValueEditor() {
    	return valueEditor;
    }
    
    /** Proxy call to the internal parameter to return it's value.  */
    public Object getValue() {
        return model.getValue();
    }

    /** Returns the parameter this editor is pointing to.  */
    public ParameterAPI getParameter() { return model; }

    /** Not sure what this is used for. This base class function is empty. */
    public String[] getTags() { return null; }

    /** Returns the value of the parameer as a String, regardless of it's true data type */
    public String getAsText() { return getValue().toString(); }

    /** Returns the focusEnabled boolean indicating this is the GUI componet with the current focus */
    public boolean isFocusEnabled() { return focusEnabled; }



    /**
     * Called when the parameter has changed independently from
     * the editor, such as with the ParameterWarningListener.
     * This function needs to be called to to update
     * the GUI component ( text field, picklsit, etc. ) with
     * the new parameter value. Implemented in subclasses.
     */
    public void refreshParamEditor() { }

    /**
     * Needs to be called by subclasses when editable widget field change fails
     * due to constraint problems. Allows rollback to the previous good value.
     */
    public void unableToSetValue( Object value ) throws ConstraintException {

        String S = C + ": unableToSetValue():";
        // if(D) System.out.println(S + "New Value = " + value.toString());

        if ( ( value != null ) && ( model != null ) ) {
            Object obj = model.getValue();
            if ( D ) System.out.println( S + "Old Value = " + obj.toString() );
            if(obj !=null){
              if (!obj.toString().equals(value.toString())) {
                model.unableToSetValue(value);
              }
            }
            else
              model.unableToSetValue(value);
        }
    }


    /**
     * Not sure what this is used for, but makes a JLabel with default values
     * and sets the text to the passed in String.
     */
    public static JLabel makeConstantEditor( String label ) {

        JLabel l = new JLabel();
        l.setPreferredSize( LABEL_DIM );
        l.setMinimumSize( LABEL_DIM );
        l.setFont( JCOMBO_FONT );
        l.setForeground( Color.blue );
        l.setBorder( CONST_BORDER );
        l.setText( label );
        return l;
    }


    /**
     * Main GUI Initialization point. This block of code is updated by JBuilder
     * when using it's GUI Editor.
     */
    protected void jbInit() throws Exception {

        // Main component
        titledBorder1 = new TitledBorder(BorderFactory.createLineBorder(FORE_COLOR,1),"");
        titledBorder1.setTitleColor(FORE_COLOR);
        titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
        titledBorder1.setTitle("Parameter Name");
        border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));


        //this.setBorder( BORDER );
        //this.setBackground( BACK_COLOR );
        this.setLayout( GBL );


        // Outermost panel
        outerPanel.setLayout( GBL );
        //outerPanel.setBackground( BACK_COLOR );
        outerPanel.setBorder(border1);

        // widgetPanel panel init
        //widgetPanel.setBackground( BACK_COLOR );
        widgetPanel.setLayout( GBL );
        widgetPanel.setMinimumSize( WIGET_PANEL_DIM );
        widgetPanel.setPreferredSize( WIGET_PANEL_DIM );


        // nameLabel panel init
        //nameLabel.setBackground( BACK_COLOR );
        nameLabel.setMaximumSize( LABEL_DIM );
        nameLabel.setMinimumSize( LABEL_DIM );
        nameLabel.setPreferredSize( LABEL_DIM );
        nameLabel.setHorizontalAlignment( SwingConstants.LEFT );
        nameLabel.setHorizontalTextPosition( SwingConstants.LEFT );
        nameLabel.setText( LABEL_TEXT );
        nameLabel.setFont( DEFAULT_LABEL_FONT );

        //if ( FORE_COLOR != null )
          //  nameLabel.setForeground( FORE_COLOR );

        // Build gui layout
        //labelPanel.add( nameLabel, NAME_LABEL_GBC );
        //outerPanel.add( labelPanel, LABLE_PANEL_GBC );
        outerPanel.add( widgetPanel, WIDGET_PANEL_GBC );


        this.add( outerPanel, OUTER_PANEL_GBC );

    }

    /** Removes the Parameter editor component from this editor.
     *  Allows this editor to be reconfigured to handle a
     *  new type of parameter.
     */
    protected void removeWidget() {
       // String S = C + ": addWidget(): ";
        if ( widgetPanel != null && valueEditor != null )
            widgetPanel.remove( valueEditor );
        valueEditor = null;
    }

    /**
     * VERY IMPORTANT function to understand this framework.
     * This function must be overidden by all subclasses. This is
     * where the particular type of editor component is added
     * to the GUI for editing the particular type of parameter. <p>
     *
     * This base class sets the widget to a simple JTextField
     * for an example of usage. This allows this editor
     * to be able to edit an unconstrained String Parameter.
     * No subclass is needed for that type of parameter. <p>
     *
     * Note: most subclasses add more complexity to this component.
     * For example, the DoubleParameterEditor makes this widget
     * componet an NumericTextField that only accepts numeric
     * characters, such as digets and a period for the decimal place.
     */
    protected void addWidget() {

        valueEditor = new JTextField();
        valueEditor.setBackground( Color.white );
        valueEditor.setMinimumSize( LABEL_DIM );
        valueEditor.setPreferredSize( LABEL_DIM );

        ( ( JTextField ) valueEditor ).setText( DATA_TEXT );
        widgetPanel.add( valueEditor, WIDGET_GBC );

    }

    /** Allows the GUI to set different borders to this editor for customization */
    public void setWidgetBorder(Border b){
        //((JTextField)valueEditor).setBorder(b);
    }

    /** Updates the name label (titled border ) of this editor with a new parameter name. */
    protected void updateNameLabel( String label ) {

        String units = model.getUnits();

        if(label == null)
          titledBorder1.setTitle("");
        else if ( ( units != null ) && !( units.equals( "" ) ) ){
            label += " (" + units + "):";
            titledBorder1.setTitle(label);
            //nameLabel.setText( label );
        }
        else{
            label += ':';
            titledBorder1.setTitle(label);
            //nameLabel.setText( label );
        }
    }

    /** Called when this editor gains the GUI focus for keyboard and mouse events. */
    public void focusGained( FocusEvent e ) {
    }

    /** Called when this editor looses the GUI focus for keyboard and mouse events. */
    public void focusLost( FocusEvent e ) {

    }


    /** Called when a key is typed in this editor. */
    public void keyTyped( KeyEvent e ) { }

    /** Called when a key is pressed in this editor. */
    public void keyPressed( KeyEvent e ) { }

    /** Called when a key was pressed and is now released in this editor. */
    public void keyReleased( KeyEvent e ) { }

    /**
     * It enables/disables the editor according to whether user is allowed to
     * fill in the values. THIS METHOD NEEDS TO BE OVERRIDDEN FOR COMPLEX ParameterEditors
     */
    public void setEnabled(boolean isEnabled) {
      valueEditor.setEnabled(isEnabled);
    }


    /**
     * return the JPanel
     * This is needed so that we can set the border or font differently
     * This function is called from IMR gui Bean and ERF Gui Bean
     * @return
     */
    public JPanel getOuterPanel() {
      return outerPanel;
    }


	public JPanel getPanel() {
		return this;
	}

}

