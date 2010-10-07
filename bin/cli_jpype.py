import os
import jpype

def startCli() :      
    # These are the lines to start up the the java <--> python bridge
    # We add the lib directory to the jar path, it expects there to be a jar
    # of the OpenSHA + gem build.
    # We also add the parent folder, so that the contents of the 'data' folder
    # Can be accessed with getResource from within java
    
    jarpath = os.path.join(os.path.abspath('..'), 'lib')
    classpath = os.path.abspath('..')
    jpype.startJVM(jpype.getDefaultJVMPath(), '-Djava.ext.dirs=%s:%s' % (jarpath, classpath))
    
    # These lines are the same as the imports in Java
    CalculatorConfigData = jpype.JClass(
	    'org.opensha.gem.GEM1.calc.gemCommandLineCalculator.CalculatorConfigData')
    CommandLineCalculator = jpype.JClass(
	    'org.opensha.gem.GEM1.calc.gemCommandLineCalculator.CommandLineCalculator')
    ErfLogicTreeData = jpype.JClass(
	    'org.opensha.gem.GEM1.calc.gemCommandLineCalculator.ErfLogicTreeData')
    GmpeLogicTreeData = jpype.JClass(
	    'org.opensha.gem.GEM1.calc.gemCommandLineCalculator.GmpeLogicTreeData')
    InputModelData = jpype.JClass(
	    'org.opensha.gem.GEM1.calc.gemCommandLineCalculator.InputModelData')
	    
    # We can instantiate python classes as python-normal
    # calculator = CommandLineCalculator()
    calcConfigData = CalculatorConfigData("CalculatorConfig.inp")
    # We can also access members of imported classes and call methods on our
    # instances of java classes.
    #calculator.doCalculation()
                                            
if __name__ == "__main__" :
    startCli()	

