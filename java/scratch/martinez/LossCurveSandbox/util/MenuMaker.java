package scratch.martinez.LossCurveSandbox.util;

import java.util.Iterator;
import java.util.TreeMap;
import java.util.Vector;

import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;

/**
 * This class is a utility for creating and managing menus for swing based
 * applications. This class is a &ldquo;static&rdquo; class and does not allow
 * for instantiation.
 * 
 * @author   
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public class MenuMaker {

	
	//---------------------------------------------------------------------------
	// Member Variables
	//---------------------------------------------------------------------------

	//---------------------------- Constant Members ---------------------------//
	
	// Menu names to create.
	public static final String FILE_MENU   = "File";
	public static final String EDIT_MENU   = "Edit";
	public static final String VIEW_MENU   = "View";
	public static final String ADV_MENU    = "Advanced";
	public static final String TOOL_MENU   = "Tools";
	public static final String HELP_MENU   = "Help";
	public static final String WINDOW_MENU = "Window"; // Required for MacOS LAF.

	//----------------------------  Static Members  ---------------------------//
	
	/**
	 * The application parent window where the application menu is placed. This
	 * is stored away for call back reference as needed so the application may
	 * always have the most recently update menu.
	 */
	private static JFrame parentFrame = null;
	
	/**
	 * A mapping of menu names to a corresponding vector of items to display in
	 * that menu. Note that a <code>JMenu</code> is a sub class of a 
	 * <code>JMenuItem</code> so in this way multi-level menues can be added to
	 * the menubar.
	 */
	private static TreeMap<String, Vector<JMenuItem>> menuMappings = null;
	
	/**
	 * A flag informing the menu maker if this menu should be optimized for
	 * the MacOS or not.
	 */
	private static boolean isMacOs = 
		(System.getProperty("os.name").toUpperCase().indexOf("MAC") != -1);
	
	//---------------------------- Instance Members ---------------------------//

	// No instance members. This class is static.
	
	//---------------------------------------------------------------------------
	// Constructors/Initializers
	//---------------------------------------------------------------------------
	
	/**
	 * Private constructor to prevent instantiation.
	 */
	private MenuMaker() { }
	
	/**
	 * This class is a static class with only private constructors (that are
	 * never called). This block is executed exactly once per runtime the very
	 * first time this class is accessed in any way.
	 */
	static {
		menuMappings = new TreeMap<String, Vector<JMenuItem>>();
	}
	
	//---------------------------------------------------------------------------
	// Public Methods
	//---------------------------------------------------------------------------

	//------------------------- Public Setter Methods  ------------------------//

	//------------------------- Public Getter Methods  ------------------------//

	//------------------------- Public Utility Methods ------------------------//

	/**
	 * Sets the parent application window that uses the menu bar created from
	 * this <code>MenuMaker</code>.
	 * 
	 * @param app The application parent window to add the menu to.
	 */
	public static void setParentFrame(JFrame app) {
		parentFrame = app;
		updateApplicationMenu();
	}
	
	/**
	 * Adds the given <code>options</code> to the application menu bar. These
	 * options are added corresponding to their identifying keys.
	 * 
	 * @param options The mapping between parent-menu names and their options.
	 */
	public static void addMenuOptions(TreeMap<String, JMenuItem> options) {
		Iterator<String> keyIter = options.keySet().iterator();
		while(keyIter.hasNext()) {
			String key = keyIter.next();
			
			String menuName =  key;
			if(WINDOW_MENU.equalsIgnoreCase(key) && !isMacOs) {
				// We're not using macOs, so put any "window" options into the
				// "view" menu instead.
				menuName = "view";
			}
			
			Vector<JMenuItem> items = menuMappings.get(menuName);
			if(items == null) {
				items = new Vector<JMenuItem>();
			}
			items.add(options.get(key));
			
			menuMappings.put(menuName, items);
		}
	}
	
	/**
	 * Flushes the current list of menu mappings into an actual menu bar and then
	 * if the <code>parentFrame</code> is not <code>null</code> then the menu
	 * bar is set as the application menu bar.
	 */
	public static void updateApplicationMenu() {
		
		JMenuBar menuBar = new JMenuBar();
		Iterator<String> keyIter = menuMappings.keySet().iterator();
		while(keyIter.hasNext()) {
			String key = keyIter.next();
			JMenu menu = new JMenu(key);
			Vector<JMenuItem> items = menuMappings.get(key);
			for(int i = 0; i < items.size(); ++i) {
				menu.add(items.get(i));
			}
			menuBar.add(menu);
		}
		
		// Update the menu in the application (if it has been set).
		if(parentFrame != null) {
			parentFrame.setJMenuBar(menuBar);
		}
	}
	
	//---------------------------------------------------------------------------
	// Private Methods
	//---------------------------------------------------------------------------

}
