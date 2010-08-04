package scratch.martinez.LossCurveSandbox.ui.gui;

import java.awt.Dimension;
import java.awt.FileDialog;
import java.awt.Toolkit;
import java.beans.PropertyChangeListener;
import java.io.FilenameFilter;
import java.util.TreeMap;

import javax.swing.JFrame;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;

import scratch.martinez.LossCurveSandbox.ui.AbstractBeanEditor;

/**
 * This is the base class that defines the most basic methods that an GUI Editor
 * must implement. When implementing an editor, one should be careful to 
 * remember that the underlying bean for an instance of the editor may be shared
 * between several (or composite) editors. This being the case, one should
 * have implement the editor such that it listens to every property of its
 * underlying bean that it edits. By following this model, if the bean's
 * property is changed by an external object, the editor will be informed of the
 * change and can act appropriately.
 * 
 * @author  
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public abstract class AbstractGuiEditor extends AbstractBeanEditor
		implements PropertyChangeListener {

	// Implementation side-effect for serialization.
	private static final long serialVersionUID = 0xA4300C1;
	
	// The title displayed on a file chooser with this editor.
	private static final String FILE_CHOOSER_TITLE = "Select a File";
	
	// The directory displayed when the file chooser is first opened.
	private static String fileChooserStartDir = System.getProperty("user.dir");
	
	/**
	 * The size of the screen. Useful for sizing and placing application windows.
	 */
	public static Dimension screenSize = 
			Toolkit.getDefaultToolkit().getScreenSize();
	
	/**
	 * See the general contract declared in the <code>BeanEditorAPI</code>
	 * interface.
	 */
	public boolean boolPrompt(String question, boolean suggestion) {
		
		// Wrap the string nicely
		question = wrapString(question, 50);

		String [] options = new String[2];
		int YES_OPTION = 0, NO_OPTION = 1;
		options[YES_OPTION] = "Yes";
		options[NO_OPTION] = "No";
		
		int answer = JOptionPane.showOptionDialog(null, question, "Question",
				JOptionPane.YES_NO_OPTION, JOptionPane.QUESTION_MESSAGE, null,
				options, options[0]);
		
		return (answer == YES_OPTION);
	}
	
	/**
	 * See the general contract declared in the <code>BeanEditorAPI</code>
	 * interface.
	 */
	public void infoPrompt(String message) {
		message = wrapString(message, 50);
		JOptionPane.showMessageDialog(null, message, "Information",
				JOptionPane.INFORMATION_MESSAGE);
		
	}
	
	/**
	 * Shows a file dialog pop-up to the user and asks for a file. The
	 * <code>fileFilter</code> can be <code>null</code> in which case any file
	 * can be selected. Otherwise the <code>fileFilter</code> will restrict which
	 * files can be chosen by the user.
	 * 
	 * @param fileFilter The file filter to apply when promping user for a file.
	 * @return The fully qualified name of the file the user selected. If user
	 * &ldquo;cancels&rdquo; the selection, then <code>null</code> is returned.
	 */
	public String getFileFromUser(FilenameFilter fileFilter) {
		// If the window editor is null, then no harm no foul.
		FileDialog chooser = new FileDialog(getWindowEditor(),
				FILE_CHOOSER_TITLE, FileDialog.LOAD);
		
		// Set the file filter.
		if(fileFilter != null) {
			chooser.setFilenameFilter(fileFilter);
		}
	
		// Set default directory to current directory.
		chooser.setDirectory(fileChooserStartDir);
		
		// Show the dialog for user to select a file.
		chooser.setVisible(true);
		
		String baseFile = chooser.getFile();
		String baseDir  = chooser.getDirectory();
		if(baseFile != null && baseDir != null) {
			// Update current directory for next call
			fileChooserStartDir = baseDir;
			// Return the selected file
			return baseDir + System.getProperty("file.separator") + baseFile;
		} else {
			return null;
		}
	}
	
	/**
	 * <p>
	 * Retrieves a mapping of menu options that should be added when this bean
	 * editor is used. The keys of this mapping represent the name of the
	 * top-level parent menu under which the corresponding menu item should
	 * appear. Note that a <code>JMenu</code> extends a <code>JMenuItem</code>
	 * and so multi-level (or nested) menus can be created using this method.
	 * </p>
	 * <p>
	 * This method should be implemented recursively such that a parent bean need
	 * only ask its immediate descendants for their menu options and any nested
	 * beans that may be unknown to the parent will also automatically expose
	 * their menu options as well.
	 * </p>
	 * <p>
	 * It is the responsibility of the top-most parent component of the
	 * application to actually create the menu bar and add it to the application.
	 * All menu items should already have action listeners and accessibility
	 * steps taken.
	 * </p>
	 * 
	 * @return
	 */
	public abstract TreeMap<String, JMenuItem> getMenuOptions();
	
	/**
	 * @return The JPanel suitable to be embedded into a larger application
	 * window. This panel contains all the required components to modify the
	 * underlying bean.
	 */
	public abstract JPanel getPanelEditor();
	
	/**
	 * @return The top-level window version of the GUI editor. This editor can
	 * be popped-up from a parent application or could possibly be an application
	 * itself. This window will contain all the components required to  modify
	 * the underlying bean and also a button to close the window (a confirm/
	 * apply, etc.. button).
	 */
	public abstract JFrame getWindowEditor();
	
	/**
	 * Instantiates and initializes the GUI components used by this editor such
	 * that after a successful call to this method the editors are ready for
	 * user interaction.
	 */
	protected abstract void initGuiEditors();

}
