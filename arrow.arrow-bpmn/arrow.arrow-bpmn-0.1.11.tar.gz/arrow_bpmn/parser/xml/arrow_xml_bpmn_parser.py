from arrow_bpmn.model.process import EventDict
from arrow_bpmn.model.task.extension.http_task import HttpTask
from arrow_bpmn.parser.xml.xml_bpmn_parser import XmlBpmnParser
from arrow_bpmn.parser.xml.xml_element import XMLElement


class ArrowXmlBpmnParser(XmlBpmnParser):

    def _parse_custom_task(self, task: XMLElement, events: EventDict):
        _type = task.get_attribute("arrow:type")
        assert _type is not None, "no task event specification found"

        if _type == "http":
            attributes = task.get_attributes()
            assert task.has_tag("bpmn:extensionElements"), "invalid http task specification"
            extension_elements = task.get_tag("bpmn:extensionElements")
            
            # parse endpoint
            assert extension_elements.has_tag("arrow:endpoint")
            endpoint = extension_elements.get_tag("arrow:endpoint")
            attributes["url"] = endpoint.get_attribute("url")
            attributes["method"] = endpoint.get_attribute("method")
            
            # parse headers
            headers = extension_elements.get_tags("arrow:httpHeader")
            headers = {header.get_attribute("key"): header.get_attribute("value") for header in headers}
            attributes["headers"] = headers
            
            # parse request expression
            if extension_elements.has_tag("arrow:requestExpression"):
                expression = extension_elements.get_tag("arrow:requestExpression")
                attributes["requestExpression"] = expression.get_text(True)

            # parse response expression
            if extension_elements.has_tag("arrow:responseExpression"):
                expression = extension_elements.get_tag("arrow:responseExpression")
                attributes["responseExpression"] = expression.get_text(True)
            
            return HttpTask(attributes)
        
        return super()._parse_custom_task(task, events)