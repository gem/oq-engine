package scratch.vipin;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.ArrayList;

import javax.swing.JPanel;

import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;

/**
 * <p>Title: RuptureFilterGuiBean.java </p>
 * <p>Description: This gui Bean allows user to select various parameters to filter
 * the ruptures from the master rupture list </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class RuptureFilterGuiBean extends JPanel {

  // various parameter names
  private final static String SECTION_PARAM_NAME = "Fault Section";
  private final static String MIN_RUP_LENTH_PARAM_NAME="Min Rupture Length";
  private final static String MAX_RUP_LENTH_PARAM_NAME="Max Rupture Length";
  private final static String MULTI_SECTION_PARAM_NAME="Only spanning more than 1 section";
  private final static String ALL = "All";
  private final static String EDITOR_TITLE="Filter Ruptures";
  // various parameters
  private StringParameter sectionParam;
  private DoubleParameter minRupLengthParam, maxRupLengthParam;
  private BooleanParameter multiSectionRuptureParam;
  private ParameterListEditor editor;

  /**
   * Section names from which user can choose the sections to plot
   * @param sectionNames
   */
  public RuptureFilterGuiBean(ArrayList sectionNames) {
    sectionNames.add(0, ALL);
    initParamsAndEditor(sectionNames);
    this.setLayout(new GridBagLayout());
    this.add(editor,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 3, 0, 3), 0, 0));
  }

  /**
   * Make all parameters and editors
   *
   * @param sectionNames
   */
  private void initParamsAndEditor(ArrayList sectionNames) {
    // parameter to allow user to choose section name
    sectionParam = new StringParameter(SECTION_PARAM_NAME, sectionNames, (String)sectionNames.get(0));
    // parameter to enter min rupture length
    minRupLengthParam = new DoubleParameter(MIN_RUP_LENTH_PARAM_NAME);
    //parameter to enter max rupture length
    maxRupLengthParam = new DoubleParameter(MAX_RUP_LENTH_PARAM_NAME);
    // parameter to specify whether only ruptures spanning more than 1 section need to be displayed
    multiSectionRuptureParam = new BooleanParameter(MULTI_SECTION_PARAM_NAME, new Boolean(false));
    // parameter list
    ParameterList paramList = new ParameterList();
    paramList.addParameter(sectionParam);
    paramList.addParameter(minRupLengthParam);
    paramList.addParameter(maxRupLengthParam);
    paramList.addParameter(multiSectionRuptureParam);
    // parameter list editor
    editor = new ParameterListEditor(paramList);
    editor.setTitle(EDITOR_TITLE);
  }

  /**
   * Get the selected section name.
   * Returns null if all sections need to be displayed
   *
   * @return
   */
  public String getSelectedSectionName() {
     String sectionName = (String)sectionParam.getValue();
     if(sectionName.equalsIgnoreCase(ALL)) sectionName = null;
     return sectionName;
  }

  /**
   * Get minimum rupture length
   * @return
   */
  public double getMinRupLength() {
    Object value  = minRupLengthParam.getValue();
    if(value==null) return Double.NaN;
    else return ((Double)value).doubleValue();
  }

  /**
   * Get maximum rupture length
   * returns Double.Nan
   * @return
   */
  public double getMaxRupLength() {
    Object value  = maxRupLengthParam.getValue();
    if(value==null) return Double.NaN;
    else return ((Double)value).doubleValue();
  }

  /**
   * Whether we need to filter only those ruptures which span across more
   * than 1 section
   *
   * @return
   */
  public boolean areOnlyMultiSectionRuptures() {
    return ((Boolean)multiSectionRuptureParam.getValue()).booleanValue();
  }

}