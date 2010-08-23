import os
import jpype

def startCli() :      
    # These are the lines to start up the the java <--> python bridge
    # We add the lib directory to the jar path, it expects there to be a jar
    # of the OpenSHA + gem build.
    jarpath = os.path.join(os.path.abspath('..'), 'lib')
    # print "xxr jarpath = " + jarpath
    jpype.startJVM(jpype.getDefaultJVMPath(), '-Djava.ext.dirs=%s' % jarpath)
    #
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
    calcConfigData = CalculatorConfigData("../data/CalculatorConfig.inp")
    # We can also access members of imported classes and call methods on our
    # instances of java classes.
    #calculator.doCalculation()
                                            
if __name__ == "__main__" :
    startCli()	

