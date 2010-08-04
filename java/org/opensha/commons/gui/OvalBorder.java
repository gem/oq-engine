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

import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.border.Border;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;

/**
 * <b>Title:</b> OvalBorder<p>
 *
 * <b>Description:</b> This class implements a Border that has rounded edges.
 * Gives a GUI a softer feel, instead of typical rectangular borders
 * around components. This class allows you to set different colors for
 * the top and left border from the bottom and right border. It draws
 * a line of 2 pixel width, and lets you set how "large" or more
 * pronounched to make the rounded edges.<p>
 *
 * <b>Note:</b> This class has a few problems with aliasing for single
 * thickness lines with small rounded corners. In other words, the corners
 * look jagged. May need to be fixed at some point in the future. For our
 * app we use the 2 pixel thick line so this jaggedness is not a problem<P>
 *
 * @ see Border
 * @author     Steven W. Rock
 * @created    February 20, 2002
 * @version    1.0
 * 
 * TODO deprecate or fix and use... main() test looks like crap
 */

public class OvalBorder implements Border {

    /**
     *  Width in pixels of the rounded corners, the higher the number, the
     *  larger the rounded corner is drawn
     */
    protected int width = 6;
    /**
     *  Height in pixels of the rounded corners, the higher the number, the
     *  larger the rounded corner is drawn
     */
    protected int height = 6;

    /** The color of the border in the top and left sides, defaults to white  */
    protected Color topColor = Color.white;

    /** The color of the border in the bottom and right sides, defaults to gray*/
    protected Color bottomColor = Color.gray;

    /**
     *  Can draw line as either single thickness or double. Set this value to
     *  true for double. Defaults to double
     */
    protected boolean thickLine = true;


    /** No-Arg constructor sets width and height = 6 for the rounded corners */
    public OvalBorder() { width = 6; height = 6; }

    /**
     * Constructor where you can set the rounded corners width and height.
     *
     * @param  w  width of rounded corners
     * @param  h  height of rounded corners
     */
    public OvalBorder( int w, int h ) {
        width = w;
        height = h;
    }


    /**
     *  Constructor where you can set the rounded corners width and height, and
     *  the colors of the top-left and bottom-right halves.
     *
     * @param  w            width of rounded corners
     * @param  h            height of rounded corners
     * @param  topColor     Color to draw the left and top sides
     * @param  bottomColor  Color to draw the right and bottom sides
     */
    public OvalBorder( int w, int h, Color topColor, Color bottomColor ) {
        width = w;
        height = h;
        this.topColor = topColor;
        this.bottomColor = bottomColor;
    }


    /** Gets the topColor used to drawn the left and top sides. */
    public java.awt.Color getTopColor() { return topColor; }
    /** Sets the topColor used to drawn the left and top sides. */
    public void setTopColor( java.awt.Color newTopColor ) { topColor = newTopColor; }

    /** gets the bottomColor used to drawn the right and bottom sides. */
    public java.awt.Color getBottomColor() { return bottomColor; }
    /** Sets the bottomColor used to drawn the right and bottom sides. */
    public void setBottomColor( java.awt.Color newBottomColor ) { bottomColor = newBottomColor; }

    /** Gets the width of rounded corners. */
    public int getWidth() { return width; }
    /** Sets the width of rounded corners. */
    public void setWidth( int newWidth ) { width = newWidth; }

    /** Gets the height of rounded corners. */
    public int getHeight() { return height; }
    /** Sets the height of rounded corners. */
    public void setHeight( int newHeight ) { height = newHeight; }

    /** If true a thick line is drawn for the borders, else a thin line is drawn. */
    public boolean isThickLine() { return thickLine; }
    /** If true a thick line is drawn for the borders, else a thin line is drawn. */
    public void setThickLine( boolean newThickLine ) { thickLine = newThickLine; }

    /**
     *  BorderAPI - Gets the borderInsets attribute of the OvalBorder object
     */
    public Insets getBorderInsets( Component c ) {
        return new Insets( height, width, height, width );
    }

    /** Returns true if the border is drawn opaque. */
    public boolean isBorderOpaque() { return true; }


    /**
     * Here is where all the work is done to draw the border. This is
     * all Java2D graphics drawing techniques. This is automatically
     * called everytime the component is redrawn to the screen.<p>
     *
     * @param  c  Component to draw border around, such as a JPanel
     * @param  g  The graphics "screen" to draw to.
     * @param  x  Upper left corner of component, x-coordinate
     * @param  y  Upper left corner of component, y-coordinate
     * @param  w  Width of the component
     * @param  h  Height of the component
     */
    public void paintBorder( Component c, Graphics g, int x, int y, int w, int h ) {

        w--;
        h--;
        g.setColor( topColor );

        g.drawLine( x, y + h - height, x, y + height );

        g.drawArc( x, y, 2 * width, 2 * height, 180, -90 );
        //g.drawArc(x+1, y+1, 2*width, 2*height, 180, -90);
        g.drawArc( x + 1, y, 2 * width, 2 * height, 180, -90 );
        //g.drawArc(x, y+1, 2*width, 2*height, 180, -90);

        g.drawLine( x + width, y, x + w - width, y );
        //g.drawLine(x+width, y+1, x+w-width, y+1);

        g.drawArc( x + w - 2 * width, y, 2 * width, 2 * height, 90, -90 );
        //g.drawArc(x+w-2*width - 1, y +1, 2*width, 2*height, 90, -90);
        g.drawArc( x + w - 2 * width - 1, y, 2 * width, 2 * height, 90, -90 );
        //g.drawArc(x+w-2*width, y +1, 2*width, 2*height, 90, -90);

        g.setColor( bottomColor );

        g.drawLine( x + w, y + height, x + w, y + h - height );
        //g.drawLine(x+w - 1, y+height, x+w - 1, y+h-height);

        g.drawArc( x + w - 2 * width, y + h - 2 * height, 2 * width, 2 * height, 0, -90 );
        //g.drawArc(x+w-2*width - 1, y+h-2*height -1, 2*width, 2*height, 0, -90);
        g.drawArc( x + w - 2 * width, y + h - 2 * height - 1, 2 * width, 2 * height, 0, -90 );
        //g.drawArc(x+w-2*width - 1, y+h-2*height , 2*width, 2*height, 0, -90);

        g.drawLine( x + width, y + h, x + w - width, y + h );
        //g.drawLine(x+width, y+h -1, x+w-width, y+h - 1);

        g.drawArc( x, y + h - 2 * height, 2 * width, 2 * height, -90, -90 );
        //g.drawArc(x + 1, y+h-2*height - 1, 2*width, 2*height, -90, -90);
        g.drawArc( x, y + h - 2 * height - 1, 2 * width, 2 * height, -90, -90 );
        //g.drawArc(x + 1, y+h-2*height, 2*width, 2*height, -90, -90);


        if ( thickLine ) {

            g.drawLine( x + 1, y + h - height, x + 1, y + height );

            g.drawArc( x + 1, y + 1, 2 * width, 2 * height, 180, -90 );
            g.drawArc( x, y + 1, 2 * width, 2 * height, 180, -90 );

            g.drawLine( x + width, y + 1, x + w - width, y + 1 );

            g.drawArc( x + w - 2 * width - 1, y + 1, 2 * width, 2 * height, 90, -90 );
            g.drawArc( x + w - 2 * width, y + 1, 2 * width, 2 * height, 90, -90 );

            g.setColor( bottomColor );

            g.drawLine( x + w - 1, y + height, x + w - 1, y + h - height );

            g.drawArc( x + w - 2 * width - 1, y + h - 2 * height - 1, 2 * width, 2 * height, 0, -90 );
            g.drawArc( x + w - 2 * width - 1, y + h - 2 * height, 2 * width, 2 * height, 0, -90 );

            g.drawLine( x + width, y + h - 1, x + w - width, y + h - 1 );

            g.drawArc( x + 1, y + h - 2 * height - 1, 2 * width, 2 * height, -90, -90 );
            g.drawArc( x + 1, y + h - 2 * height, 2 * width, 2 * height, -90, -90 );

        }
    }


    /** Tester function that makes a frame and draws a OvalBorder on it. */
    public static void main( String[] args ) {
        JFrame frame = new JFrame( "Custom Border: OvalBorder" );
        JLabel label = new JLabel( "OvalBorder" );
        ( ( JPanel ) frame.getContentPane() ).setBorder( new CompoundBorder(
                new EmptyBorder( 10, 10, 10, 10 ), new OvalBorder( 20, 20, Color.blue, Color.black ) ) );
        frame.getContentPane().add( label );
        frame.setBounds( 0, 0, 300, 150 );
        frame.setVisible( true );
    }

}
