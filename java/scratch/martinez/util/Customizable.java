package scratch.martinez.util;

import javax.swing.JComponent;

import scratch.martinez.beans.PropertiesBean;

/**
 * <strong>Title:</strong> Customizable<br />
 * <strong>Description:</strong>A public interface that makes a class customizable within the
 * jQuake framework.  There is a single method required to be implemented for a class to be
 * customizable and that is <code>getPropertyPane()</code>.  A customizable object in the
 * jQuake framework allows a simple method for an end user to set their personal preferences
 * for the application properties.  For example, a user can select where they want to do their
 * data mining (local or remote), or could optionally set up proxy information if required.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</a>
 * @see PropertyHandler
 * @see PropertiesBean
 */
public interface Customizable {
	/**
	 * This is the only method required for a class to be considered customizable from the
	 * perspective of the jQuake framework.  This JComponent (generally a JPanel or JScrollPane),
	 * should contain other elements that allow the user to customize certain features of the
	 * implementing class.  For example, this panel might contain a labeled text box so
	 * that the user can type in the location of a preferred directory to store output files.
	 * 
	 * The implementation should NOT assume that any other class will listen to changes in 
	 * any parameters.  The implementing class should listen to changes made to any of this
	 * panel's objects and react accordingly (i.e. set the new value in the <code>PropertyHandler</code>.
	 * 
	 * @return The self-listening pane that can be added to the a <code>PropertiesBean</code>.
	 * @see PropertyHandler
	 */
	public JComponent getPropertyPane();
}
