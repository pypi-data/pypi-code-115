#interface objects
from .InterfaceObjects import ASG,StopCondition
#import helper functions
from .HelperFunctions import *

#-----------------------------------------------------------------------------------------------------------
#
#   ASG extension
#
#       TODO:
#               - Discuss: Do we need to provide the rules in the getASG()
#               - Discuss: Do we need to provide the rules in the setASG()
#               - Discuss: Can we assume that the assembly system is in place when performing setASG()
#               - Discuss: Do we need seperate functions to UPDATE and ADD DFA rules?
#
# -----------------------------------------------------------------------------------------------------------

def getASG(AssemblySystemName,model,KBPath):
    """
          Function to fetch the Assembly Sequence Generation (ASG) configuration using the name as identifier.
          The function returns an interface block of the ASG

          :param string AssemblySystemName: Name identifier of the assemlbySystem
          :param object model: Metamodel instance model
          :param string KBPath: Absolute path to the metamodel instance model

          :return object ASGModel: Interface object of the ASG (-1 = error)
    """

    found = 0
    InterfaceObject = ASG(None) #interface object placeholder
    if len(model.includesAssemblySystem.items) != 0:
        #match the assemblySystem by Name
        for assemblySystem in model.includesAssemblySystem.items:
            if AssemblySystemName == assemblySystem.hasName:
                found=1
                #fetch ASG and setup ASG return
                ASG_temp = assemblySystem.hasAssemblyAlgorithmConfiguration
                InterfaceObject.Name = ASG_temp.hasName
                InterfaceObject.Description = ASG_temp.hasDescription
                InterfaceObject.ProcessingType = ASG_temp.hasProcessingType.name

                # -- ASG GENERATOR --
                try:
                        InterfaceObject.Generator=[ASG_temp.hasSinglePartGenerator.hasName, 'SinglePartGenerator']
                except:
                    x = "No SinglePartGenerator available"
                try:
                        InterfaceObject.Generator=[ASG_temp.hasMultiPartGenerator.hasName, 'MultiPartGenerator']
                except:
                    x = "No MultiPartGenerator available"

                # try-catch structure to fetch the ASG SELECTOR
                try:
                        InterfaceObject.Selector=[ASG_temp.hasDefaultSelector.hasName, 'DefaultSelector']
                except:
                    x = "No Default selector available"
                try:
                        InterfaceObject.Selector=[ASG_temp.hasRuleSelector.hasName, 'RuleSelector']             #TODO: discuss if we need to fetch the rules
                except:
                    x = "No Rule selector available"

                # try-catch structure to fetch the ASG EVALUATOR
                try:
                        InterfaceObject.Evaluator=[ASG_temp.hasUniformEvaluator.hasName,'UniformEvaluator']
                except:
                    x = "No uniform evalutor available"
                try:
                        InterfaceObject.Evaluator=[ASG_temp.hasRuleEvaluator.hasName, 'RuleEvaluator']
                except:
                    x = "No Rule selector available"

                # -- Terminator --
                terms = []
                try:
                    for terminator in ASG_temp.hasTerminator.hasStopCriterion.items:
                        # -- stopconditions --
                        s = StopCondition(None, terminator.hasName, terminator.hasDescription,terminator.hasValue, terminator.hasStopCriterion.name)

                        #add to criteria
                        terms.append(s)
                    InterfaceObject.StopConditionList = terms
                except:
                    x = "No Stop criterion available"

            else:
                x = 1

        if found:
            return InterfaceObject
        else:
            return -2
    else:
        return -2  # no assembly systems!

def updateASG(AssemblySystemName,interfaceObject,model,KBPath):
    """
          Function to update the  complete Assembly Sequence Generation (ASG) configuration using the name as identifier.
          The ASG interface object is used to interface with the function.
          The function returns whether or not the function is performed correctly

          :param string AssemblySystemName: Name identifier of the assemlbySystem
          :param object ASGModel: Interface object of the ASG
          :param object model: Metamodel instance model
          :param string KBPath: Absolute path to the metamodel instance model

          :return int Error: -1 = error, 1= function performed correcly
    """

    found = 0
    if len(model.includesAssemblySystem.items) != 0:
        #match the assemblySystem by Name
        for assemblySystem in model.includesAssemblySystem.items:
            if AssemblySystemName == assemblySystem.hasName:
                found=1
                # -- ASG setup --
                assemblySystem.hasAssemblyAlgorithmConfiguration.hasName = interfaceObject.Name
                assemblySystem.hasAssemblyAlgorithmConfiguration.hasDescription = interfaceObject.Description
                assemblySystem.hasAssemblyAlgorithmConfiguration.hasProcessingType = interfaceObject.ProcessingType

                # -- ASG GENERATOR --
                try:
                    assemblySystem.hasAssemblyAlgorithmConfigurationhasSinglePartGenerator.hasSinglePartGenerator.hasName = interfaceObject.Generator[0]
                except:
                    x = "No SinglePartGenerator available"
                try:
                    assemblySystem.hasAssemblyAlgorithmConfigurationhasSinglePartGenerator.hasMultiPartGenerator.hasName = interfaceObject.Generator[0]
                except:
                    x = "No MultiPartGenerator available"

                # -- ASG SELECTOR --
                try:
                    assemblySystem.hasAssemblyAlgorithmConfigurationhasSinglePartGenerator.hasDefaultSelector.hasName =  interfaceObject.Selector[0]
                except:
                    x = "No Default selector available"
                try:
                    assemblySystem.hasAssemblyAlgorithmConfigurationhasSinglePartGenerator.hasRuleSelector.hasName = interfaceObject.Selector[0]
                    #TODO: discuss if we need to update the rules or via dedicated function!
                except:
                    x = "No Rule selector available"

                # -- ASG EVALUATOR --
                try:
                    assemblySystem.hasAssemblyAlgorithmConfigurationhasSinglePartGenerator.hasUniformEvaluator.hasName = interfaceObject.Evaluator[0]
                except:
                    x = "No uniform evalutor available"
                try:
                    assemblySystem.hasAssemblyAlgorithmConfigurationhasSinglePartGenerator.hasRuleEvaluator.hasName = interfaceObject.Evaluator[0]
                    # TODO: discuss if we need to update the rules or via dedicated function!
                except:
                    x = "No Rule selector available"



                # -- Terminator container --
                for terminator in assemblySystem.hasAssemblyAlgorithmConfiguration.hasTerminator.hasStopCriterion.items:
                    for stp in interfaceObject.StopConditionList:
                        if stp.Name==terminator.hasName:
                            terminator.hasName=stp.Name
                            terminator.hasDescription=stp.Description
                            terminator.hasValue=stp.Value
                            terminator.hasStopCriterion=stp.StopCriteria

            else:
                return -1

        if found:
            updateKBv6(KBPath, model)
            return 1
        else:
            return -1
    else:
        return -1  # no Optimization Problem!

def setASG( AssemblySystemName, InterfaceObject,model,KBPath,path_ecore,MM,API):
    """
          Function to set a new Assembly Sequence Generation (ASG) configuration to a new AssemblySystem
          The performance interface object is used to interface with the function.
          The function returns whether or not the function is performed correctly

          :param object ASGModel: Interface object of the ASG model
          :param object model: Metamodel instance model
          :param string KBPath: Absolute path to the metamodel instance model
          :param string KBPath: Absolute path to the metamodel ecore model

          :return int Error: -1 = error, 1= function performed correcly
    """

    # -- create new AssemblySystem --
    AS = API.create_connected("AssemblySystem")
    AS.hasName = AssemblySystemName
    # -- create new ASG --
    ASG_ = API.create("AssemblyAlgorithmConfiguration")
    ASG_.hasName = InterfaceObject.Name
    ASG_.hasDescription = InterfaceObject.Description
    #ASG.hasProcessingType = InterfaceObject.ProcessingType                 #TODO: check how to set this

    if 'SinglePartGenerator' in InterfaceObject.Generator[1]:
        # -- ASG GENERATOR --
        try:
            ASG_.hasSinglePartGenerator.hasName = InterfaceObject.Generator[0]
        except:
            x = "No SinglePartGenerator available"
            # -- create new class if not existing --
            g_ = API.create("SinglePartGenerator")
            g_.hasName = InterfaceObject.Generator[0]
            ASG_.hasSinglePartGenerator = g_

    if 'MultiPartGenerator' in InterfaceObject.Generator[1]:
        # -- ASG GENERATOR --
        try:
            ASG_.hasMultiPartGenerator.hasName = InterfaceObject.Generator[0]
        except:
            x = "No MultiPartGenerator available"
            # -- create new class if not existing --
            g_ = API.create("MultiPartGenerator")
            g_.hasName = InterfaceObject.Generator[0]
            ASG_.hasMultiPartGenerator = g_

    if 'DefaultSelector' in InterfaceObject.Selector[1]:
        # -- ASG SELECTOR --
        try:
            ASG_.hasDefaultSelector.hasName = InterfaceObject.Selector[0]
        except:
            x = "No Default selector available"
            # -- create new class if not existing --
            g_ = API.create("DefaultSelector")
            g_.hasName = InterfaceObject.Selector[0]
            ASG_.hasDefaultSelector = g_

    if 'RuleSelector' in InterfaceObject.Selector[1]:
        # -- ASG SELECTOR --
        try:
            ASG_.hasRuleSelector.hasName = InterfaceObject.Selector[0]
        except:
            x = "No RuleSelector available"
            # -- create new class if not existing --
            g_ = API.create("RuleSelector")
            g_.hasName = InterfaceObject.Selector[0]
            ASG_.hasRuleSelector = g_

    if 'UniformEvaluator' in InterfaceObject.Evaluator[1]:
        # -- ASG EVALUATOR --
        try:
            ASG_.hasUniformEvaluator.hasName = InterfaceObject.Evaluator[0]
        except:
            x = "No uniform evaluator available"
            # -- create new class if not existing --
            g_ = API.create("UniformEvaluator")
            g_.hasName = InterfaceObject.Evaluator[0]
            ASG_.hasDefaultSelector = g_

    if 'RuleEvaluator' in InterfaceObject.Evaluator[1]:
        # -- ASG EVALUATOR --
        try:
            ASG_.hasRuleEvaluator.hasName = InterfaceObject.Evaluator[0]
        except:
            x = "No RuleEvaluator available"
            # -- create new class if not existing --
            g_ = API.create("RuleEvaluator")
            g_.hasName = InterfaceObject.Evaluator[0]
            ASG_.hasRuleEvaluator = g_

    # -- stop conditions --
    terminator_container = API.create("Terminator")
    terminator_container.hasName = "Default"
    ASG_.hasTerminator = terminator_container
    for stp in InterfaceObject.StopConditionList:
        #terminator = API.create_custom(e_class="StopCriterion",parent=terminator_container)
        terminator= API.create_noPlatformRoot("StopCriterion")
        terminator.hasName = stp.Name
        terminator.hasDescription = stp.Description
        terminator.hasValue = stp.Value
        #terminator.hasStopCriterion = stp.StopCriteria         #TODO:assigns currently a string!
        terminator_container.hasStopCriterion.append(terminator)

    AS.hasAssemblyAlgorithmConfiguration = ASG_

    updateKBv6(KBPath,model)