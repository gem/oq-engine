package junk;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;

import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 * <b>Title:</b> ParameterEditorFactory<p>
 *
 * <b>Description:</b> This factory is used to create the appropiate
 * Editor for a Parameter based on the String type accessed by getType() that
 * every Parameter subclass implements. This class uses a few rules to
 * generate the complete package and class name of the editor. This class is
 * used by the ParameterListEditor and makes it so you can create new Parameter
 * classes without having to recompile the ParameterListEditor or this Factory class.
 * In other words the ParameterEditors are dynamically loaded at runtime based on the
 * paramter type. There is no hardcoding of editor information here.  <p>
 *
 * <b>Note:</b> This class is currently uses only static functions and variables.
 * We may need to change this in the future if many clients try to set the
 * searchPaths. No synchronization has been built in yet. Susceptable
 * to multiple threads changing the searchPaths.<p>
 *
 * <b>Note: </b> This class only knows about ParameterEditor class. By creating
 * the subclass full package and class name dynamically this class can use java
 * Reflection API to dynamically create any subclass type, without knowing
 * any details about it. This allows new editors to be designed in the future
 * and added to the framework without modifying this Factory class nor
 * our GUI components that use this Factory class to generate the Editors.
 * Very flexible framework.
 *
 * @author Steven W. Rock
 * @version 1.0
 */
@Deprecated
public class ParameterEditorFactory {

    /* *******************/
    /** @todo  Variables */
    /* *******************/


    /** Class name for debugging. */
    protected final static String C = "ParameterEditorFactory";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** First path this Factory looks for Editor Classes */
    protected final static String DEFAULT_PATH = "org.opensha.commons.param.editor";

    /**
     * Additional search paths ( i.e. corresponds to java pacakges ) that the
     * programmer can add to. Currently the org/scec/sha/propagation is
     * an additional path.
     */
    protected static String[] searchPaths;


    /**
     * The constructor is made private because all functions are static. No
     * need to initialize with a constructor.
     */
    private ParameterEditorFactory() { }

    /**
     * Allows the programmer to add additional searchpaths for locating java
     * classes. Currently the org/scec/sha/propagation is an additional path.
     */
    public static void setSearchPaths(String[] searchPaths){
        ParameterEditorFactory.searchPaths = searchPaths;
    }
    /** Returns the current search paths for java files. */
    public static String[] getSearchPaths(){ return searchPaths; }

    /**
     * Main API function call for this Factory class. You simply pass in the
     * parameter you wish to create an editor for. This function then calls
     * getType() on the parameter to build an editor class name. Then a full package
     * name is created by trying each search path sequentially to locate the
     * editor Class. Finally the constructor is called on the String full classname
     * using java Reflection API. The parameter is set in the editor and the
     * editor is returned as an ParameterEditor.
     *
     */
     public static ParameterEditor getEditor(ParameterAPI param) throws ParameterException {

        // Debugging
        String S = C + ": getEditor(): ";
        if(D) System.out.println('\n' + S + "Starting");

        // Initial Type
        String type = param.getType();
        String name = param.getName();

        if(D) System.out.println(S + "Type = " + type);
        if(D) System.out.println(S + "Name = " + name);


        // Build full classname of the editor
        Class c = getClass(type);

        // Instantiate instance
        Object obj = getClassInstance(c);

        // Cast to ParameterEditor and add param to editor
        if(obj instanceof ParameterEditor){
            ParameterEditor editor = (ParameterEditor)obj;
            editor.setParameter(param);
            return editor;
        }
        else{ throw new ParameterException(S + "Created class doesn't extend AbstractParameterEditor: " + c.getName()); }
   }

    /**
     * The Class class of the editor found on the
     * search path is instantiated with a no-argument constructor
     */
    private static Object getClassInstance(Class c) throws ParameterException{

        // Debugging
        String S = C + ": getClassInstance(): ";

        try{

            // Create Constructor class instance and instantiate new class
            // equivalent to new org.opensha.sha.param.editor.StringEditor()
            Constructor con = c.getConstructor( new Class[]{} );
            Object obj = con.newInstance( new Object[]{} );

            return obj;
        }
        catch(NoSuchMethodException e){ throw new ParameterException(S + e.toString() ); }
        catch(InvocationTargetException e){ throw new ParameterException(S + e.toString() ); }
        catch(IllegalAccessException e){ throw new ParameterException(S + e.toString() ); }
        catch(InstantiationException e){ throw new ParameterException(S + e.toString() ); }


    }

    /**
     * Locates Editors by prepending a package name to the type, then adding Editor to
     * end. Default path checked is org.opensha.param.editor. If the editor is not
     * found in here, an attempt is made in each path set in the user defined
     * searchPaths array. The first match is returned. If none found a Parameter
     * Exception is thrown
     */
    private static Class getClass(String shortClassName) throws ParameterException{

        // Debugging
        String S = C + ": getClass(): ";
        String classname = "";

        if( ( searchPaths != null) || (searchPaths.length > 0) ){

            for(int i = 0; i < searchPaths.length; i++){

                classname = searchPaths[i]  + '.' + shortClassName + "Editor";

                try{

                    // Create the Class class - i.e. static reflector class
                    // into Editor class methods, constructors, fields
                    Class c = Class.forName(classname);
                    if(D) System.out.println(S + "Class = " + classname);

                    return c;

                }
                catch(ClassNotFoundException e){} // Can't find in path, try next path

            }

        }

        StringBuffer b = new StringBuffer();
        b.append(S + "Failed package names search path\n");

        if( ( searchPaths != null) || (searchPaths.length > 0) ){
            for(int i = 0; i < searchPaths.length; i++){
                b.append(searchPaths[i] + '\n');
            }
        }


        System.out.println( b.toString() );

        // Can't find in any paths at all
        throw new ParameterException(S + "Unable to locate editor in search paths: " + shortClassName + "Editor");

    }
}
