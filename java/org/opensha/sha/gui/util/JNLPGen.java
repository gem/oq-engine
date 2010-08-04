package org.opensha.sha.gui.util;

import java.awt.Color;
import java.awt.Font;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;

import javax.imageio.ImageIO;

import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.opensha.commons.util.IconGen;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.commons.util.ServerPrefs;
import org.opensha.commons.util.XMLUtils;
import org.opensha.sha.gui.HazardCurveLocalModeApplication;
import org.opensha.sha.gui.HazardCurveServerModeApplication;
import org.opensha.sha.gui.HazardSpectrumLocalModeApplication;
import org.opensha.sha.gui.HazardSpectrumServerModeApplication;
import org.opensha.sha.gui.ScenarioShakeMapApp;
import org.opensha.sha.gui.ScenarioShakeMapLocalModeCalcApp;
import org.opensha.sha.imr.attenRelImpl.gui.AttenuationRelationshipApplet;

public class JNLPGen {
	
	private static final String jnlpDir = "ant" + File.separator + "jnlp";
	private static final String webRoot = "http://opensha.usc.edu/apps/opensha";
	
	private static final String vendor = "OpenSHA";
	private static final String homepage = "http://www.opensha.org";
	
	private static final String iconsDirName = "icons";
	
	private Class<?> theClass;
	private String shortName;
	private String title;
	private String iconText;
	private int xmxMegs = 1024;
	private static ServerPrefs prefs = ServerPrefUtils.SERVER_PREFS;
	private boolean startMenu = true;
	private boolean desktop = true;
	private boolean allowOffline = true;
	
	private ArrayList<IconEntry> icons;
	
	public JNLPGen(Class<?> theClass, String shortName, String title, String iconText, boolean allowOffline) {
		System.out.println("Creating JNLP for: " + theClass.getName());
		this.theClass = theClass;
		this.shortName = shortName;
		this.title = title;
		this.iconText = iconText;
		this.allowOffline = allowOffline;
	}
	
	private void generateAppIcons(String baseDir) throws IOException {
		String iconDir = baseDir + File.separator + iconsDirName;
		File dirFile = new File(iconDir);
		if (!dirFile.exists())
			dirFile.mkdirs();
		
		IconGen gen = new IconGen(IconGen.loadLogoIcon(), iconText, Font.SANS_SERIF, Color.WHITE, Color.BLACK);
		if (allowOffline)
			gen.setUpperRightImage(IconGen.loadLocalIcon());
		else
			gen.setUpperRightImage(IconGen.loadServerIcon());
		icons = new ArrayList<IconEntry>();
		int[] sizes = { 128, 64, 48, 32, 16 };
		for (int size : sizes) {
			BufferedImage icon = gen.getIcon(size, size);
			String fileName = shortName + "_" + size + "x" + size + ".png";
			ImageIO.write(icon, "png", new File(iconDir + File.separator + fileName));
			icons.add(new IconEntry(iconsDirName + "/" + fileName, size, size));
		}
	}
	
	public static void setDefaultServerPrefs(ServerPrefs prefs) {
		JNLPGen.prefs = prefs;
	}
	
	public void setServerPrefs(ServerPrefs prefs) {
		JNLPGen.prefs = prefs;
	}
	
	private String getDistType() {
		return prefs.getBuildType();
	}
	
	public void setAllowOffline(boolean allowOffline) {
		this.allowOffline = allowOffline;
	}
	
	public void writeJNLPFile() throws IOException {
		writeJNLPFile(jnlpDir);
	}
	
	public void writeJNLPFile(String dir) throws IOException {
		Document doc = createDocument();
		
		File dirFile = new File(dir);
		if (!dirFile.exists())
			dirFile.mkdirs();
		
		String fileName = dir + File.separator + shortName + ".jnlp";
		System.out.println("Writing JNLP to: " + fileName);
		
		XMLUtils.writeDocumentToFile(fileName, doc);
	}
	
	public Document createDocument() {
		Document doc = DocumentHelper.createDocument();
		
		doc.addElement("jnlp");
		Element root = doc.getRootElement();
		
		// root attributes
		root.addAttribute("spec", "6.0+");
		String codeBaseURL = webRoot + "/" + shortName + "/" + getDistType();
		root.addAttribute("codebase", codeBaseURL);
		root.addAttribute("href", shortName + ".jnlp");
		
		// information
		Element infoEl = root.addElement("information");
		Element titleEl = infoEl.addElement("title");
		titleEl.addText(title);
		Element vendorEl = infoEl.addElement("vendor");
		vendorEl.addText(vendor);
		// shortcuts
		if (startMenu || desktop) {
			Element shortcutEl = infoEl.addElement("shortcut");
			shortcutEl.addAttribute("online", !allowOffline + "");
			if (desktop)
				shortcutEl.addElement("desktop");
			if (startMenu) {
				Element menuEl = shortcutEl.addElement("menu");
				menuEl.addAttribute("submenu", vendor);
			}
		}
		infoEl.addElement("homepage").addAttribute("href", homepage);
		if (allowOffline) {
			// offline-allowed
			infoEl.addElement("offline-allowed");
		}
		// icons
		if (icons != null) {
			for (IconEntry icon : icons) {
				Element iconEl = infoEl.addElement("icon");
				iconEl.addAttribute("href", icon.url);
				iconEl.addAttribute("width", icon.width+"");
				iconEl.addAttribute("height", icon.height+"");
				if (icon.kind != null && icon.kind.length() > 0)
					iconEl.addAttribute("kind", icon.kind);
			}
		}
		
		// resources
		Element resourcesEl = root.addElement("resources");
		Element javaEl = resourcesEl.addElement("java");
		javaEl.addAttribute("version", "1.6+");
		javaEl.addAttribute("java-vm-args", "-Xmx"+xmxMegs+"M");
		javaEl.addAttribute("href", "http://java.sun.com/products/autodl/j2se");
		Element jarEl = resourcesEl.addElement("jar");
		String jarName = shortName + ".jar";
		jarEl.addAttribute("href", jarName);
		jarEl.addAttribute("main", "true");
		
		// application-desc
		Element appDestEl = root.addElement("application-desc");
		appDestEl.addAttribute("name", title);
		appDestEl.addAttribute("main-class", theClass.getName());
		
		// update
		Element updateEl = root.addElement("update");
		updateEl.addAttribute("check", "timeout");
		
		// security
		Element securityEl = root.addElement("security");
		securityEl.addElement("all-permissions");
		
		return doc;
	}
	
	private class IconEntry {
		
		String url;
		String kind;
		int width;
		int height;
		
		public IconEntry(String url, int width, int height) {
			this(url, width, height, null);
		}
		
		public IconEntry(String url, int width, int height, String kind) {
			this.url = url;
			this.width = width;
			this.height = height;
			this.kind = kind;
		}
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		String outputDir = null;
		ServerPrefs[] prefsToBuild = ServerPrefs.values();
		if (args.length == 0) {
			outputDir = JNLPGen.jnlpDir;
		} else if (args.length == 1 || args.length == 2) {
			outputDir = args[0];
			if (args.length == 2) {
				String buildType = args[1];
				prefsToBuild = new ServerPrefs[1];
				prefsToBuild[0] = ServerPrefs.fromBuildType(buildType);
			}
		} else {
			System.err.println("USAGE: JNLPGen [outputDir [build_type]]");
			System.exit(2);
		}
		ArrayList<JNLPGen> appsToBuild = new ArrayList<JNLPGen>();
		/*		Hazard Curve				*/
		appsToBuild.add(new JNLPGen(HazardCurveLocalModeApplication.class,
				"HazardCurveLocal", "Hazard Curve Local Mode Application", "HC", true));
		appsToBuild.add(new JNLPGen(HazardCurveServerModeApplication.class,
				"HazardCurveServer", "Hazard Curve Server Mode Application", "HC", false));
		/*		Hazard Spectrum				*/
		appsToBuild.add(new JNLPGen(HazardSpectrumLocalModeApplication.class,
				"HazardSpectrumLocal", "Hazard Spectrum Local Mode Application", "HS", true));
		appsToBuild.add(new JNLPGen(HazardSpectrumServerModeApplication.class,
				"HazardSpectrumServer", "Hazard Spectrum Server Mode Application", "HS", false));
		/*		Scenario ShakeMap			*/
		appsToBuild.add(new JNLPGen(ScenarioShakeMapLocalModeCalcApp.class,
				"ScenarioShakeMapLocal", "Scenario ShakeMap Local Mode Application", "SM", true));
		appsToBuild.add(new JNLPGen(HazardSpectrumServerModeApplication.class,
				"ScenarioShakeMapServer", "Scenario ShakeMap Server Mode Application", "SM", false));
		/*		Attenuation Relationship	*/
		appsToBuild.add(new JNLPGen(AttenuationRelationshipApplet.class,
				"AttenuationRelationship", "Attenuation Relationship Application", "AR", true));
		
		for (ServerPrefs myPrefs : prefsToBuild) {
			setDefaultServerPrefs(myPrefs);
			String distOutDir = outputDir + File.separator + myPrefs.getBuildType();
			for (JNLPGen app : appsToBuild) {
				app.generateAppIcons(distOutDir);
				app.writeJNLPFile(distOutDir);
			}
		}
	}

}
