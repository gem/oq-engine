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

package org.opensha.commons.gui;

import java.awt.Color;
import java.awt.Component;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.LayoutManager;
import java.awt.SystemColor;

import javax.swing.BorderFactory;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.border.LineBorder;
import javax.swing.border.TitledBorder;

/**
 * <b>Title:</b> LabeledBorderPanel<p>
 *
 * <p>Description:</b> A JPanel GUI widget that contains a TitledBorder,
 * and a JScrollPane that let's you add any internal Java Compoenent inside it.
 * Useful for creating Parameter Editors. All Parameter Editors subclass
 * this class. This is a generic component so it was useful
 * to pull this common functionality out of the ParameterEditors
 * and make that a subclass. <p>
 *
 * The main usage is to add a component to the editor panel using one
 * of the add() functions listed below.<p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class LabeledBorderPanel extends JPanel{

    protected final static String C = "LabeledBorderPanel";
    protected final static boolean D = false;

    protected JScrollPane jScrollPane1 = new JScrollPane();
    protected JPanel editorPanel = new JPanel();

    protected SidesBorder border = null;
    protected SidesBorder border2 = null;

    protected static GridBagLayout GBL = new GridBagLayout();

    protected String title;

    protected Color borderColor = new Color( 80, 80, 133 );

    protected boolean addDefault = true;
    JPanel mainPanel = new JPanel();
    LineBorder border1;
    TitledBorder titledBorder1;


    /**
     * Creates a new JPanel with the specified layout manager and buffering
     * strategy.
     *
     * @param layout  the LayoutManager to use
     * @param isDoubleBuffered  a boolean, true for double-buffering, which
     *        uses additional memory space to achieve fast, flicker-free
     *        updates
     */
    public LabeledBorderPanel(LayoutManager layout, boolean isDoubleBuffered) {
        super(layout, isDoubleBuffered);
        try { jbInit(); }
        catch ( Exception e ) { e.printStackTrace(); }
        if( editorPanel != null ) editorPanel.setLayout(layout);
    }

    /**
     * Create a new buffered JPanel with the specified layout manager
     *
     * @param layout  the LayoutManager to use
     */
    public LabeledBorderPanel(LayoutManager layout) {
        super(layout);
        try { jbInit(); }
        catch ( Exception e ) { e.printStackTrace(); }
        if( editorPanel != null ) editorPanel.setLayout(layout);
    }

    /**
     * Creates a new <code>JPanel</code> with <code>FlowLayout</code>
     * and the specified buffering strategy.
     * If <code>isDoubleBuffered</code> is true, the <code>JPanel</code>
     * will use a double buffer.
     *
     * @param layout  the LayoutManager to use
     * @param isDoubleBuffered  a boolean, true for double-buffering, which
     *        uses additional memory space to achieve fast, flicker-free
     *        updates
     */
    public LabeledBorderPanel(boolean isDoubleBuffered) {
        super(isDoubleBuffered);
        try { jbInit(); }
        catch ( Exception e ) { e.printStackTrace(); }
        if( editorPanel != null ) editorPanel.setLayout(new FlowLayout());
    }

    /**
     * Creates a new <code>JPanel</code> with a double buffer
     * and a flow layout.
     */
    public LabeledBorderPanel() {
        super();
        try { jbInit(); }
        catch ( Exception e ) { e.printStackTrace(); }

        if( editorPanel != null ) editorPanel.setLayout(new FlowLayout());
    }

    /**
     * Sets the layout manager for this container.
     * @param mgr the specified layout manager
     * @see #doLayout
     * @see #getLayout
     */
    public void setLayout(LayoutManager mgr) {
        if( addDefault ) super.setLayout(mgr);
        else if( editorPanel != null ) editorPanel.setLayout(mgr);

    }

    /**
     *  Sets the title in this boxPanel
     *
     * @param  newTitle  The new title value
     */
    public void setTitle( String newTitle ) {
        title = newTitle;
        if( titledBorder1 != null ) titledBorder1.setTitle( title );
    }

    /**
     *  Sets the borderColor for the borders in this boxPanel
     *
     * @param  newBorderColor  The new borderColor value
     */
    public void setBorderColor( Color newBorderColor ) {
        borderColor = newBorderColor;
        if( border1 != null )
            border1 = (LineBorder)BorderFactory.createLineBorder( newBorderColor, 1 );
        if( titledBorder1 != null ) {
            titledBorder1.setBorder( border1 );
            titledBorder1.setTitleColor(newBorderColor);
        }
    }


    /**
     *  Gets the title in this boxPanel
     *
     * @return    The title value
     */
    public String getTitle() { return title; }

    /**
     *  Gets the borderColor of this boxPanel
     *
     * @return    The borderColor value
     */
    public Color getBorderColor() { return borderColor; }

    public void setTitleJustification(int justification){
        if( titledBorder1 != null ) titledBorder1.setTitleJustification(justification);
    }

    public void setTitlePosition(int position){
        if( titledBorder1 != null ) titledBorder1.setTitlePosition(position);
    }

    public void setTitleFont(Font font){
        if( titledBorder1 != null ) titledBorder1.setTitleFont( font );
    }

    /**
     * Initializes the GUI components and layout
     * @throws Exception
     */
    protected void jbInit() throws Exception {

        addDefault = true;
        border1 = (LineBorder)BorderFactory.createLineBorder(SystemColor.activeCaption,1);
        titledBorder1 = new TitledBorder(border1,"Title");
        titledBorder1.setTitleColor(SystemColor.activeCaption);
        titledBorder1.setTitleFont( new java.awt.Font("Dialog", 1, 11) );


        this.setBackground( Color.white );
        this.setFont(new java.awt.Font("Dialog", 1, 11));
        this.setBorder( border2 );
        this.setLayout( GBL );

        editorPanel.setLayout( GBL );

        editorPanel.setBackground( Color.white );
        jScrollPane1.setBorder( null );

        mainPanel.setBackground(Color.white);
        mainPanel.setBorder(titledBorder1);
        mainPanel.add(jScrollPane1, new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));

        add(mainPanel,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));

        jScrollPane1.getViewport().add( editorPanel, ( Object ) null );
        addDefault = false;
    }


    /**
     * Appends the specified component to the end of this container.
     * This is a convenience method for {@link #addImpl}.
     *
     * @param     comp   the component to be added
     * @see #addImpl
     * @return    the component argument
     */
    public Component add(Component comp) {
        if( addDefault ) return super.add(comp);
        else return editorPanel.add(comp);
    }

    /**
     * Adds the specified component to this container.
     * This is a convenience method for {@link #addImpl}.
     * <p>
     * This method is obsolete as of 1.1.  Please use the
     * method <code>add(Component, Object)</code> instead.
     */
    public Component add(String name, Component comp) {
        if( addDefault ) return super.add(name, comp);
        else return editorPanel.add(name, comp);
    }

    /**
     * Adds the specified component to this container at the given
     * position.
     * This is a convenience method for {@link #addImpl}.
     *
     * @param     comp   the component to be added
     * @param     index    the position at which to insert the component,
     *                   or <code>-1</code> to append the component to the end
     * @return    the component <code>comp</code>
     * @see #addImpl
     * @see	  #remove
     */
    public Component add(Component comp, int index) {
        if( addDefault ) return super.add(comp, index);
        else return editorPanel.add(comp, index);
    }


    /**
     * Adds the specified component to the end of this container.
     * Also notifies the layout manager to add the component to
     * this container's layout using the specified constraints object.
     * This is a convenience method for {@link #addImpl}.
     *
     * @param     comp the component to be added
     * @param     constraints an object expressing
     *                  layout contraints for this component
     * @see #addImpl
     * @see       LayoutManager
     * @since     JDK1.1
     */
    public void add(Component comp, Object constraints) {
        if( addDefault ) super.add(comp, constraints);
        else editorPanel.add(comp, constraints); }


    /**
     * Adds the specified component to this container with the specified
     * constraints at the specified index.  Also notifies the layout
     * manager to add the component to the this container's layout using
     * the specified constraints object.
     * This is a convenience method for {@link #addImpl}.
     *
     * @param comp the component to be added
     * @param constraints an object expressing layout contraints for this
     * @param index the position in the container's list at which to insert
     * the component. -1 means insert at the end.
     * component
     * @see #addImpl
     * @see #remove
     * @see LayoutManager
     */
    public void add(Component comp, Object constraints, int index) {
        if( addDefault ) super.add(comp, constraints, index);
        else editorPanel.add(comp, constraints, index);
    }


}
