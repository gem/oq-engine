/**
 * 
 */
package org.opensha.refFaultParamDb.vo;

import org.dom4j.Element;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * @author vipingupta
 *
 */
public class DeformationModelSummary  implements java.io.Serializable, XMLSaveable {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	public static final String XML_METADATA_NAME = "DeformationModelSummary";

	private int deformationModelId;
	private String deformationModelName;
	private FaultModelSummary faultModel;
	private Contributor contributor;

	public Contributor getContributor() {
		return contributor;
	}
	public void setContributor(Contributor contributor) {
		this.contributor = contributor;
	}
	public int getDeformationModelId() {
		return deformationModelId;
	}
	public void setDeformationModelId(int deformationModelId) {
		this.deformationModelId = deformationModelId;
	}
	public String getDeformationModelName() {
		return deformationModelName;
	}
	public void setDeformationModelName(String deformationModelName) {
		this.deformationModelName = deformationModelName;
	}
	public FaultModelSummary getFaultModel() {
		return faultModel;
	}
	public void setFaultModel(FaultModelSummary faultModel) {
		this.faultModel = faultModel;
	}
	public Element toXMLMetadata(Element root) {

		Element el = root.addElement(XML_METADATA_NAME);

		el.addAttribute("deformationModelId", deformationModelId + "");
		el.addAttribute("deformationModelName", deformationModelName);

		// add the contributor
		el = this.contributor.toXMLMetadata(el);

		// add the fault model
		el = this.faultModel.toXMLMetadata(el);

		return root;
	}

	public static DeformationModelSummary fromXMLMetadata(Element el) {

		int id = Integer.parseInt(el.attributeValue("deformationModelId"));
		String name = el.attributeValue("deformationModelName");

		FaultModelSummary fm = FaultModelSummary.fromXMLMetadata(el.element(FaultModelSummary.XML_METADATA_NAME));
		Contributor cont = Contributor.fromXMLMetadata(el.element(Contributor.XML_METADATA_NAME));

		DeformationModelSummary def = new DeformationModelSummary();

		def.setDeformationModelId(id);
		def.setDeformationModelName(name);
		def.setContributor(cont);
		def.setFaultModel(fm);

		return def;
	}

}
