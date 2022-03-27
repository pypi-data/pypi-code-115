from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.terraform.checks.resource.base_resource_value_check import BaseResourceValueCheck


class AppServiceJavaVersion(BaseResourceValueCheck):
    def __init__(self):
        name = "Ensure that 'Java version' is the latest, if used to run the web app"
        id = "CKV_AZURE_83"
        supported_resources = ['azurerm_app_service']
        categories = [CheckCategories.GENERAL_SECURITY]
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources,
                         missing_block_result=CheckResult.PASSED)

    def get_inspected_key(self):
        return "site_config/[0]/java_version/[0]"

    def get_expected_value(self):
        return '11'


check = AppServiceJavaVersion()
