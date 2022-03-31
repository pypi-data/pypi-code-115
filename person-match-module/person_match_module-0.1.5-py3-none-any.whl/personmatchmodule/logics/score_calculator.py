from typing import Optional, List, Dict, Any

from rapidfuzz import fuzz

from personmatchmodule.models.constants import Attribute
from personmatchmodule.models.rule import Rule


class ScoreCalculator:
    @staticmethod
    def initialize_score(rules: List[Rule]) -> None:
        for rule in rules:
            rule.score = 0.0

    @staticmethod
    def calculate_score(
        rules: List[Rule], data_1: Dict[str, Any], data_2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Calculate matching scores for ALL rules between FHIR Person-Person, or Person-Patient, or Person/Patient-AppUser
        :param rules: generated rules by RulesGenerator
        :param data_1: Dictionary of Pii data for FHIR Person/Patient data, or AppUser data
        :param data_2: Dictionary of Pii data for FHIR Person/Patient data, or AppUser data
        :return: list of dictionary for rules score results for all rules
        """

        rules_score_results: List[Dict[str, Any]] = []

        for rule in rules:
            rule_score_result = ScoreCalculator.calculate_score_for_rule(
                rule, data_1, data_2
            )
            if rule_score_result is not None:
                rules_score_results.append(rule_score_result)

        return rules_score_results

    @staticmethod
    def calculate_score_for_rule(
        rule: Rule, data_1: Dict[str, Any], data_2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate a matching score for one rule between FHIR Person-Person, or Person-Patient, or Person/Patient-AppUser
        :param rule: one rule in the generated rules by RulesGenerator
        :param data_1: Dictionary of Pii data for FHIR Person/Patient data, or AppUser data
        :param data_2: Dictionary of Pii data for FHIR Person/Patient data, or AppUser data
        :return: Dictionary of 1 rule score result
        """

        id_data_1: Optional[Any] = data_1.get(Attribute.ID)
        id_data_2: Optional[Any] = data_2.get(Attribute.ID)
        if not (id_data_1 and id_data_2):
            return None

        score_avg: float = 0.0
        for attribute in rule.attributes:
            val_1: Optional[Any] = data_1.get(attribute)
            val_2: Optional[Any] = data_2.get(attribute)

            if val_1 and val_2:
                # calculate exact string match on "trimmed lower" string values
                score_avg += fuzz.ratio(
                    str(val_1).strip().lower(), str(val_2).strip().lower()
                )

        score_avg /= len(rule.attributes)
        rule.score = score_avg

        rule_score_result: Dict[str, Any] = {
            Attribute.ID + "_1": str(id_data_1),
            Attribute.ID + "_2": str(id_data_2),
            Attribute.RULE_NAME: rule.name,
            Attribute.RULE_SCORE: rule.score,
        }

        return rule_score_result
