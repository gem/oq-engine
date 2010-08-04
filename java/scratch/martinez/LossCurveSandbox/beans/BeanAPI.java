package scratch.martinez.LossCurveSandbox.beans;

import java.io.Serializable;

/**
 * <p>
 * Declaring a class to be a &ldquo;Bean&rdquo; requires that it implement this
 * interface. Classes that do not implement this interface should not be
 * considered a bean and bean editors should not accept them as such. This
 * interface has minimal methods and/or fields and serves primarily to identify
 * the semantics of a bean.
 * </p>
 * <p>
 * To start, all beans should follow the official JavaBeans API specification
 * from Sun Mircosystems:<br />
 * <a href="http://java.sun.com/products/javabeans/docs/spec.html"
 *   title="JavaBeans">http://java.sun.com/products/javabeans/docs/spec.html</a>
 * <br />
 * Of principle interest is supporting introspection of the bean class and
 * exposing all member variables via getter and setter methods.
 * </p>
 * <p>
 * As per the the JavaBeans specification, bean properties may be either
 * bound, constrained, or both. If such a binding or constraint exists on a
 * bean's property, then it is the responsibility of the <em>bean</em> to
 * trigger these events before/after (as appropriate) updating the its 
 * internal state.
 * </p>
 * 
 * @author 
 * <a href="mailto:emartinez@usgs.gov?subject=NSHMP%20Application%20Question">
 * Eric Martinez
 * </a>
 */
public interface BeanAPI extends Serializable {
	
	
}
