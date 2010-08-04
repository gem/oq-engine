package org.opensha.nshmp.sha.gui.beans;

/**
 * <strong>Title</strong>: GuiBeanAPI<br />
 * <strong>Description</strong>: This interface provides a super flexible method for implementing
 * a Graphical User Interface Java Bean.  The idea behind this interface is that under varying
 * situations the same bean functionality might want to be visualized in a variety of ways.  For
 * instance, perhaps sometimes you want the bean to appear in a stand-alone frame, while other times
 * you may want the bean to appear as a button that when clicked, can visualize itself in some
 * useful method.  The goal of this interface is to allow a bean to be written once and then
 * visualized in any number of ways.  While this interface provides a suggestive list of possible
 * visualization names, this in no way should limit a developer to think these are the only ways
 * in which a bean might be visualized.  Additionally, not all beans need to be able to visualize
 * themselves in any or all of the methods listed below.  Good documentation on the implementing
 * class should clarify which visualizations are supported.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * 
 */
public interface GuiBeanAPI {
	/** Use this to visualize a <code>APPLICATION</code> instance of the bean */
	public static final int APPLICATION = 0;
	/** Use this to visualize a <code>APPLET</code> instance of the bean */
	public static final int APPLET = 1;
	/** Use this to visualize a <code>WEB</code> instance of the bean */
	public static final int WEB = 2;
	/** Use this to visualize a <code>BUTTON</code> instance of the bean */
	public static final int BUTTON = 3;
	/** Use this to visualize a <code>EMBED</code> instance of the bean */
	public static final int EMBED = 4;
	/** Use this to visualize a <code>SPLASH</code> instance of the bean */
	public static final int SPLASH = 5;
	/** Use this to visualize a <code>MENUOPT</code> instance of the bean */
	public static final int MENUOPT = 6;
	
	/**
	 * Creates a visualization that can be used in any application type
	 * that returns <code>true</code> with a call to </code>isVisualizationSupported(type)</code>.
	 * 
	 * @param type An <code>int</code> defining the type of application visualization desired.
	 * @return The visualization of the GuiBean.  This might be a <code>JComponent</code> in 
	 * the case of an applet/application, but might just be an HTML <code>String</code> in the
	 * case of a web application.  Implementation can vary greatly.
	 * @throws IllegalArgumentException If <code>isVisualizationSupported(type)</code> returns false.
	 */
	public abstract Object getVisualization(int type) throws IllegalArgumentException;
	
	/**
	 * @return The fully qualified class name of the visualization object returned
	 * by <code>getVisualization</code>.  If the given type is not supported, then 
	 * <code>null<code> is returned.
	 * 
	 * @param type The type of visualization desired.
	 */
	public abstract String getVisualizationClassName(int type);
	
	/**
	 * @param type The type of application the visualization is desired for.
	 * @return True if the visualization type is available, false otherwise.
	 */
	public abstract boolean isVisualizationSupported(int type);
	
}
