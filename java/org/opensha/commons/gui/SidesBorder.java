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
import java.awt.Graphics;
import java.awt.Insets;
import java.io.Serializable;

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.border.Border;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;

/**
 *  <b>Title:</b> SidesBorder<p>
 *
 *  <b>Description:</b> This class implements a Border where you can set any side color
 *  individually. You can also set on or off the drawing of any side. Especially
 *  useful to give the illusion of an underline. Setting the top and sides
 *  border to the same color as the background panel, users only see the bottom
 *  border.<p>
 *
 *  This class's data is basically 4 colors, and 4 booleans that indicate
 * weither to draw a particular side or not, along with the corresponding
 * getXXX() and setXXX() javabean functions. <p>
 *
 * @author     Steven W. Rock
 * @created    February 20, 2002
 * @version    1.0
 */

public class SidesBorder implements Border, Serializable {

    /** Top side of the border color */
    Color topColor = new Color( 120, 160, 100 );
    /** Bottom side of the border color */
    Color bottomColor = Color.yellow;
    /** Left side of the border color */
    Color leftColor = Color.red;
    /** Right side of the border color */
    Color rightColor = Color.blue;

    /** determines the height of the corner arcs on the border */
    private int height = 0;
    /** determines the width of the corner arcs on the border */
    private int width = 0;

    /** Boolean whether to draw the left side of the border */
    private boolean drawLeft = true;
    /** Boolean whether to draw the right side of the border */
    private boolean drawRight = true;
    /** Boolean whether to draw the top of the border  */
    private boolean drawTop = true;
    /** Boolean whether to draw the bottom of the border */
    private boolean drawBottom = true;


    /** No-Arg constructor - all sides drawn, all sides different color */
    public SidesBorder() { }


    /**
     *  Constructor that let's you set each side's color. By setting all
     * sides the same, this border acts just like a LineBorder.
     *
     * @param  topColor     Color for the top side of the border
     * @param  bottomColor  Color for the bottom side of the border
     * @param  leftColor    Color for the left side of the border
     * @param  rightColor   Color for the right side of the border
     */
    public SidesBorder( Color topColor, Color bottomColor,
                        Color leftColor, Color rightColor
    ) {
        this.topColor = topColor; this.bottomColor = bottomColor;
        this.leftColor = leftColor; this.rightColor = rightColor;
    }


    /** Sets the color for the left side of the border. */
    public void setLeftColor( Color a ) { leftColor = a; }
    /** Gets the color for the left side of the border. */
    public Color getLeftColor() { return leftColor; }

    /** Sets the color for the right side of the border. */
    public void setRightColor( Color a ) { rightColor = a; }
    /** Gets the color for the right side of the border. */
    public Color getRightColor() { return rightColor; }

    /** Sets the color for the top side of the border. */
    public void setTopColor( Color a ) { topColor = a; }
    /** Gets the color for the top side of the border. */
    public Color getTopColor() { return topColor; }

    /** Sets the color for the bottom side of the border. */
    public void setBottomColor( Color a ) { bottomColor = a; }
    /** Gets the color for the bottom side of the border. */
    public java.awt.Color getBottomColor() {  return bottomColor; }


    /** Gets the width of the corner arcs on the border */
    public int getWidth() { return width; }
    /** Sets the width of the corner arcs on the border */
    public void setWidth( int a ) { width = a; }

    /** Gets the height of the corner arcs on the border */
    public int getHeight() { return height; }
    /** Sets the height of the corner arcs on the border */
    public void setHeight( int a ) { height = a; }


    /** Flag true or false whether to draw the left side of the border */
    public void setDrawLeft( boolean a ) { drawLeft = a; }
    /** Returns true if the left border will be drawn or false otherwise. */
    public boolean isDrawLeft() { return drawLeft; }

    /** Flag true or false whether to draw the right side of the border */
    public void setDrawRight( boolean a ) { drawRight = a; }
    /** Returns true if the right border will be drawn or false otherwise. */
    public boolean isDrawRight() { return drawRight; }

    /** Flag true or false whether to draw the top side of the border */
    public void setDrawTop( boolean a ) { drawTop = a; }
    /** Returns true if the top border will be drawn or false otherwise. */
    public boolean isDrawTop() { return drawTop; }

    /** Flag true or false whether to draw the bottom side of the border */
    public void setDrawBottom( boolean a ) { drawBottom = a; }
    /** Returns true if the bottom border will be drawn or false otherwise. */
    public boolean isDrawBottom() { return drawBottom; }


    /** BorderAPI - Gets the borderInsets attribute of the SidesBorder object */
    public Insets getBorderInsets( Component c ) {
        return new Insets( height, width, height, width );
    }

    /** BorderAPI - Returns true if the border is opaque */
    public boolean isBorderOpaque() {  return true; }









    /**
     *  Here is where all the work is done to draw the border. This is
     * all Java2D graphics drawing techniques. This is automatically
     * called everytime the component is redrawn to the screen.<p>
     *
     * This draw function is broken up into 4 sections, one for each side.
     * If the boolean drawSide for that particular side is false, that
     * section is skipped. Left and right sides draw a line, while the
     * top and bottom draw a line and the corner arcs to give the side
     * a rounded appearance.<p>
     *
     * @param  c  The component that the border is painted to
     * @param  g  Graphics being drawn to
     * @param  x
     * @param  y
     * @param  w
     * @param  h
     */
    public void paintBorder(
            Component c,
            Graphics g,
            int x, int y, int w, int h ) {
        w--;
        h--;

        if ( isDrawTop() ) {
            g.setColor( topColor );

            if ( width > 0 || height > 0 ) {
                g.drawArc( x, y, 2 * width, 2 * height, 180, -90 );
                g.drawArc( x + w - 2 * width, y, 2 * width, 2 * height, 90, -90 );
            }

            g.drawLine( x + width, y, x + w - width, y );
        }

        if ( isDrawLeft() ) {
            g.setColor( leftColor );
            g.drawLine( x, y + h - height, x, y + height );
        }

        if ( isDrawBottom() ) {
            g.setColor( bottomColor );
            if ( width > 0 || height > 0 ) {
                g.drawArc( x + w - 2 * width, y + h - 2 * height, 2 * width, 2 * height, 0, -90 );
                g.drawArc( x, y + h - 2 * height, 2 * width, 2 * height, -90, -90 );
            }
            g.drawLine( x + width, y + h, x + w - width, y + h );
        }

        if ( isDrawRight() ) {
            g.setColor( rightColor );
            g.drawLine( x + w, y + height, x + w, y + h - height );
        }
    }



    /** Tester function to see the border in action. Shows usage for this class. */
    public static void main( String[] args ) {
        JFrame frame = new JFrame( "Custom Border: SideBorder" );
        JLabel label = new JLabel( "SideBorder" );
        ( ( JPanel ) frame.getContentPane() ).setBorder( new CompoundBorder(
                new EmptyBorder( 10, 10, 10, 10 ), new SidesBorder( Color.blue,
                Color.black, Color.red, Color.yellow ) ) );
        frame.getContentPane().add( label );
        frame.setBounds( 0, 0, 300, 150 );
        frame.setVisible( true );
    }


    /** Prints out state of the border variable */
    public String toString() {

        StringBuffer b = new StringBuffer( "SidesBorder:\n" );
        b.append( "\tDraw Top = " );
        b.append( drawTop );
        b.append( "\tDraw Bottom = " );
        b.append( drawBottom );
        b.append( "\tDraw Left = " );
        b.append( drawLeft );
        b.append( "\tDraw Right = " );
        b.append( drawRight );
        return b.toString();
    }
}
