from typing import Any, Dict, List

from personmatchmodule.logics.rules_generator import RulesGenerator
from personmatchmodule.logics.score_calculator import ScoreCalculator
from personmatchmodule.models.constants import Attribute
from personmatchmodule.models.rule import Rule


def test_person_one_to_one_match() -> None:
    person_1: Dict[str, Any] = {
        Attribute.ID: "unitypoint-b3a42xc8",
        Attribute.NAME_FAMILY: "bourne",
        Attribute.NAME_GIVEN: "James ",
        Attribute.GENDER: "MALE",
        Attribute.BIRTH_DATE: "1980-09-17",
        Attribute.BIRTH_DATE_YEAR: "1980",  # parsed from birth date
        Attribute.BIRTH_DATE_MONTH: "09",  # parsed from birth date
        Attribute.BIRTH_DATE_DAY: "17",  # parsed from birth date
        Attribute.ADDRESS_LINE_1: "363 Mackerline St",
        Attribute.ADDRESS_LINE_1_ST_NUM: "363",  # parsed from address
        Attribute.ADDRESS_POSTAL_CODE: "34239",
        Attribute.EMAIL: "jbourne@gmail.com",
        Attribute.EMAIL_USERNAME: "jborune",  # parsed from the email
        Attribute.PHONE: "7770003333",
        Attribute.PHONE_AREA: "777",  # parsed from phone
        Attribute.PHONE_LOCAL: "000",  # parsed from phone
        Attribute.PHONE_LINE: "3333",  # parsed from phone
        Attribute.IS_ADULT_TODAY: "true",  # calculated by today's date - birth date >= 18 yrs old
        Attribute.SSN: "",  # parsed from identifier.value
        Attribute.META_SECURITY_CLIENT_SLUG: "unitypoint",  # parsed from meta.security access
    }

    person_2: Dict[str, Any] = {
        Attribute.ID: "unitypoint-73bvy14ka0",
        Attribute.NAME_FAMILY: "BORNE",
        Attribute.NAME_GIVEN: " JAMES ",
        Attribute.GENDER: "male",
        Attribute.BIRTH_DATE: "1980-09-17",
        Attribute.BIRTH_DATE_YEAR: "1980",  # parsed from birth date
        Attribute.BIRTH_DATE_MONTH: "09",  # parsed from birth date
        Attribute.BIRTH_DATE_DAY: "17",  # parsed from birth date
        Attribute.ADDRESS_LINE_1: "363 mackerline st.",
        Attribute.ADDRESS_LINE_1_ST_NUM: "363",  # parsed from address
        Attribute.ADDRESS_POSTAL_CODE: "34239",
        Attribute.EMAIL: "jbourne@hotmail.com",
        Attribute.EMAIL_USERNAME: "jborune",  # parsed from the email
        Attribute.PHONE: "7770003355",
        Attribute.PHONE_AREA: "777",  # parsed from phone
        Attribute.PHONE_LOCAL: "000",  # parsed from phone
        Attribute.PHONE_LINE: "3355",  # parsed from phone
        Attribute.IS_ADULT_TODAY: "true",  # calculated by today's date - birth date >= 18 yrs old
        Attribute.SSN: "555992222",
        Attribute.META_SECURITY_CLIENT_SLUG: "unitypoint",
    }

    rules: List[Rule] = RulesGenerator.generate_rules()

    # match on first rule
    rule_score_result = ScoreCalculator.calculate_score_for_rule(
        rules[0], person_1, person_2
    )
    assert (
        rule_score_result is not None
        and rule_score_result.get(Attribute.ID + "_1") is not None
        and rule_score_result.get(Attribute.RULE_SCORE) is not None
    )
    print(rule_score_result)

    # match on all rules
    rules_score_results: List[Dict[str, Any]] = ScoreCalculator.calculate_score(
        rules, person_1, person_2
    )
    assert len(rules_score_results) == len(rules)
    print(rules_score_results)

    # calculate the final score
    final_score: float = 0.0
    for result in rules_score_results:
        final_score += float(str(result.get(Attribute.RULE_SCORE)))
    final_score /= len(rules)
    print(f"FINAL SCORE: {final_score}")

    # SUGGESTION
    # based on the calculated final score, in 0-100 scale,
    #  the caller categorize and assign the FHIR AssuranceLevel when creating data linkage,
    #  https://www.hl7.org/fhir/valueset-identity-assuranceLevel.html#expansion
    #  "level1" (the lowest): 0.0 - 25.0 for little or no confidence in the asserted identity's accuracy
    #  "level2"             : 25.0 - 50.0 for some confidence
    #  "level3"             : 50.0 - 80.0 for high confidence
    #  "level4" (the highest): 80.0 - 100.0 for very high confidence
