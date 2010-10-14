package util;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;

/**
 * This class contains utilities used by tests. For instance, private no-arg
 * constructors show up in Corbetura as not being covered. However, they can be
 * hit using reflection so utility methods are provided herein to reduce
 * repetition.
 * 
 * @author Peter Powers
 * @version $Id:$
 */
public class TestUtils {

    /* Private no-arg constructor invokation via reflection. */
    public static Object callPrivateNoArgConstructor(final Class<?> cls)
            throws InstantiationException, IllegalAccessException,
            InvocationTargetException {
        final Constructor<?> c = cls.getDeclaredConstructors()[0];
        c.setAccessible(true);
        final Object n = c.newInstance((Object[]) null);
        return n;
    }

}
