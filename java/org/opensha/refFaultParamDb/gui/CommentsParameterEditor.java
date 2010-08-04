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

package org.opensha.refFaultParamDb.gui;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.awt.event.FocusEvent;

import javax.swing.BorderFactory;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingConstants;
import javax.swing.border.TitledBorder;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.WarningException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 * <b>Title:</b> CommnetsParameterEditor<p>
 *
 * <b>Description:</b>   This allows the input of multi line comments by the user.
 *
 * @author Vipin Gupta, Nitin Gupta
 * @version 1.0
 */
public class CommentsParameterEditor extends ParameterEditor
{

    /** Class name for debugging. */
    protected final static String C = "CommentsParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;
    protected final static Dimension WIGET_PANEL_DIM = new Dimension( 140, 100 );
    protected final static GridBagConstraints WIDGET_GBC = new GridBagConstraints(
      0, 0, 1, 1, 1.0, 0.0, 10, GridBagConstraints.BOTH, new Insets( 1, 5, 0, 1 ), 0, 0 );
    protected final static GridBagConstraints WIDGET_PANEL_GBC = new GridBagConstraints(
      0, 1, 1, 1, 1.0, 0.0, 10, GridBagConstraints.BOTH, ZERO_INSETS, 0, 0 );

    /** No-Arg constructor calls parent constructor */
    public CommentsParameterEditor() { super(); }

    /**
     * Constructor that sets the parameter that it edits. An
     * Exception is thrown if the model is not an String Parameter <p>
     */
     public CommentsParameterEditor(ParameterAPI model) throws Exception {

        super(model);

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if ( (model != null ) && !(model instanceof StringParameter))
            throw new Exception( S + "Input model parameter must be a StringParameter.");
          refreshParamEditor();
        //this.setParameter(model);
        if(D) System.out.println(S.concat("Ending"));

    }

    /** This is where the JTextArea is defined and configured. */
    protected void addWidget() {

        String S = C + ": addWidget(): ";
        if(D) System.out.println(S + "Starting");

        valueEditor = new JTextArea();
        ((JTextArea)valueEditor).setLineWrap(true);
        ((JTextArea)valueEditor).setWrapStyleWord(true);

        valueEditor.setBorder(ETCHED);
        valueEditor.setFont(this.DEFAULT_FONT);

        valueEditor.addFocusListener( this );
        JScrollPane scrollPane = new JScrollPane(valueEditor);
        scrollPane.setMinimumSize( WIGET_PANEL_DIM );
        scrollPane.setPreferredSize( WIGET_PANEL_DIM );

        widgetPanel.add(scrollPane, ParameterEditor.WIDGET_GBC);
        widgetPanel.setBackground(null);
        widgetPanel.validate();
        widgetPanel.repaint();
        if(D) System.out.println(S + "Ending");
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
           this.setLayout( GBL );


           // Outermost panel
           outerPanel.setLayout( GBL );
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
           outerPanel.add( widgetPanel, WIDGET_PANEL_GBC );

           this.add( outerPanel, OUTER_PANEL_GBC );

       }





       /**
        * Called when the user clicks on another area of the GUI outside
        * this editor panel. This synchornizes the editor text field
        * value to the internal parameter reference.
        */
       public void focusLost(FocusEvent e) {

           String S = C + ": focusLost(): ";
           if(D) System.out.println(S + "Starting");

           super.focusLost(e);

           focusLostProcessing = false;
           if( keyTypeProcessing == true ) return;
           focusLostProcessing = true;

           String value = ((JTextArea) valueEditor).getText();
           try {
             if(value.indexOf('\'')>=0)
               JOptionPane.showMessageDialog(this,"Single quotes are not allowed in comments field\n"+
                                             "Changing all single quotes to double quotes");
             value=value.replace('\'','"');
             String d = "";
             if( !value.equals( "" ) ) d = value;
             setValue(d);
             refreshParamEditor();
             valueEditor.validate();
             valueEditor.repaint();
           }
           catch (ConstraintException ee) {
               if(D) System.out.println(S + "Error = " + ee.toString());

               Object obj = getValue();
               if( obj != null )
                   ((JTextArea) valueEditor).setText(obj.toString());
               else ((JTextArea) valueEditor).setText( "" );

               if( !catchConstraint ){ this.unableToSetValue(value); }
               focusLostProcessing = false;
           }
           catch (WarningException ee){
               focusLostProcessing = false;
               refreshParamEditor();
               valueEditor.validate();
               valueEditor.repaint();
           }


           focusLostProcessing = false;
           if(D) System.out.println(S + "Ending");

       }


    /** Sets the parameter to be edited. */
    public void setParameter(ParameterAPI model) {
        String S = C + ": setParameter(): ";
        if(D) System.out.println(S.concat("Starting"));

        super.setParameter(model);
        ((JTextArea) valueEditor).setToolTipText("No Constraints");

        String info = model.getInfo();
        if( (info != null ) && !( info.equals("") ) ){
            this.nameLabel.setToolTipText( info );
        }
        else this.nameLabel.setToolTipText( null);


        if(D) System.out.println(S.concat("Ending"));
    }

    /**
     * Updates the JTextArea string with the parameter value. Used when
     * the parameter is set for the first time, or changed by a background
     * process independently of the GUI. This could occur with a ParameterChangeFail
     * event.
     */
    public void refreshParamEditor(){
      String string = (String)model.getValue();
      ((JTextArea)valueEditor).setText(string);
    }
}
