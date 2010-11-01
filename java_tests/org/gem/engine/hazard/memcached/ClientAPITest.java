package org.gem.engine.hazard.memcached;

import static org.junit.Assert.assertEquals;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

import org.junit.Test;

/**
 * Sample JavaToJava memcached tests (probably useless in our context) just to
 * verify how the API works.
 * 
 * @author Andrea Cerisara
 */
public class ClientAPITest extends BaseMemcachedTest {

    public static class AReallyCoolObject implements Serializable {

        private static final long serialVersionUID = -4185818094252288027L;

        private final Double x;
        private final Double y;

        public AReallyCoolObject(Double x, Double y) {
            this.x = x;
            this.y = y;
        }

        @Override
        public boolean equals(Object obj) {
            if (!(obj instanceof AReallyCoolObject)) {
                return false;
            }

            AReallyCoolObject other = (AReallyCoolObject) obj;
            return other.x.equals(x) && other.y.equals(y);
        }

    }

    @Test
    public void canStoreAndRetrieveASimpleType() {
        client.set("KEY", EXPIRE_TIME, "VALUE");
        assertEquals("VALUE", client.get("KEY"));
    }

    @Test
    public void canStoreAndRetrieveAList() {
        List<Double> results = new ArrayList<Double>();
        results.add(1.0);
        results.add(2.0);
        results.add(3.0);

        client.set("KEY", EXPIRE_TIME, results);
        assertEquals(results, client.get("KEY"));
    }

    @Test
    public void canStoreAndRetrieveAComplexType() {
        client.set("KEY", EXPIRE_TIME, new AReallyCoolObject(1.0, 2.0));
        assertEquals(new AReallyCoolObject(1.0, 2.0), client.get("KEY"));
    }

}
