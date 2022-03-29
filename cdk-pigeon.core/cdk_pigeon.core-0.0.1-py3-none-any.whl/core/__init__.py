'''
# Pigeon

This is a cheaper version of AWS Synthetics Canary. Head to my [blog post](https://thomasstep.com/blog/why-do-aws-synthetics-canaries-cost-so-much) to read more about the inspiration for this CDK Construct.

Pigeon is meant to be dead simple. It creates a Lambda Function that runs on a schedule and optionally alerts an email if the Lambda fails. Everything created is exposed, so if you want to create an alert different than the default, everything is there for you to do it.

## Props

`schedule: events.Schedule`

`lambdaFunctionProps: lambda.FunctionProps`

`lambdaTargetProps?: targets.LambdaFunctionProps`

`alertOnFailure?: boolean`

`emailAddress?: string`

## Properties

`lambdaFunction!: lambda.Function`

`rule!: events.Rule`

`alarm?: cloudwatch.Alarm`

`topic?: sns.Topic`
'''
import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

from ._jsii import *

import aws_cdk.aws_cloudwatch
import aws_cdk.aws_events
import aws_cdk.aws_events_targets
import aws_cdk.aws_lambda
import aws_cdk.aws_sns
import constructs


class Pigeon(
    constructs.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-pigeon.Pigeon",
):
    '''
    :stability: experimental
    '''

    def __init__(
        self,
        scope: constructs.Construct,
        id: builtins.str,
        *,
        lambda_function_props: aws_cdk.aws_lambda.FunctionProps,
        schedule: aws_cdk.aws_events.Schedule,
        alert_on_failure: typing.Optional[builtins.bool] = None,
        email_address: typing.Optional[builtins.str] = None,
        lambda_target_props: typing.Optional[aws_cdk.aws_events_targets.LambdaFunctionProps] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param lambda_function_props: 
        :param schedule: 
        :param alert_on_failure: (experimental) User can do this on their own or let pigeon handle it. Flipping this switch only turns on SNS alerting. Use emailAddress for an actual notification.
        :param email_address: 
        :param lambda_target_props: (experimental) Let the user pass this in because timing is highly dependent on the schedule. Example: { deadLetterQueue: queue, maxEventAge: cdk.Duration.minutes(1), retryAttempts: 2, }

        :stability: experimental
        '''
        props = PigeonProps(
            lambda_function_props=lambda_function_props,
            schedule=schedule,
            alert_on_failure=alert_on_failure,
            email_address=email_address,
            lambda_target_props=lambda_target_props,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="lambdaFunction")
    def lambda_function(self) -> aws_cdk.aws_lambda.Function:
        '''
        :stability: experimental
        '''
        return typing.cast(aws_cdk.aws_lambda.Function, jsii.get(self, "lambdaFunction"))

    @lambda_function.setter
    def lambda_function(self, value: aws_cdk.aws_lambda.Function) -> None:
        jsii.set(self, "lambdaFunction", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="rule")
    def rule(self) -> aws_cdk.aws_events.Rule:
        '''
        :stability: experimental
        '''
        return typing.cast(aws_cdk.aws_events.Rule, jsii.get(self, "rule"))

    @rule.setter
    def rule(self, value: aws_cdk.aws_events.Rule) -> None:
        jsii.set(self, "rule", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="alarm")
    def alarm(self) -> typing.Optional[aws_cdk.aws_cloudwatch.Alarm]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[aws_cdk.aws_cloudwatch.Alarm], jsii.get(self, "alarm"))

    @alarm.setter
    def alarm(self, value: typing.Optional[aws_cdk.aws_cloudwatch.Alarm]) -> None:
        jsii.set(self, "alarm", value)

    @builtins.property # type: ignore[misc]
    @jsii.member(jsii_name="topic")
    def topic(self) -> typing.Optional[aws_cdk.aws_sns.Topic]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[aws_cdk.aws_sns.Topic], jsii.get(self, "topic"))

    @topic.setter
    def topic(self, value: typing.Optional[aws_cdk.aws_sns.Topic]) -> None:
        jsii.set(self, "topic", value)


@jsii.data_type(
    jsii_type="cdk-pigeon.PigeonProps",
    jsii_struct_bases=[],
    name_mapping={
        "lambda_function_props": "lambdaFunctionProps",
        "schedule": "schedule",
        "alert_on_failure": "alertOnFailure",
        "email_address": "emailAddress",
        "lambda_target_props": "lambdaTargetProps",
    },
)
class PigeonProps:
    def __init__(
        self,
        *,
        lambda_function_props: aws_cdk.aws_lambda.FunctionProps,
        schedule: aws_cdk.aws_events.Schedule,
        alert_on_failure: typing.Optional[builtins.bool] = None,
        email_address: typing.Optional[builtins.str] = None,
        lambda_target_props: typing.Optional[aws_cdk.aws_events_targets.LambdaFunctionProps] = None,
    ) -> None:
        '''
        :param lambda_function_props: 
        :param schedule: 
        :param alert_on_failure: (experimental) User can do this on their own or let pigeon handle it. Flipping this switch only turns on SNS alerting. Use emailAddress for an actual notification.
        :param email_address: 
        :param lambda_target_props: (experimental) Let the user pass this in because timing is highly dependent on the schedule. Example: { deadLetterQueue: queue, maxEventAge: cdk.Duration.minutes(1), retryAttempts: 2, }

        :stability: experimental
        '''
        if isinstance(lambda_function_props, dict):
            lambda_function_props = aws_cdk.aws_lambda.FunctionProps(**lambda_function_props)
        if isinstance(lambda_target_props, dict):
            lambda_target_props = aws_cdk.aws_events_targets.LambdaFunctionProps(**lambda_target_props)
        self._values: typing.Dict[str, typing.Any] = {
            "lambda_function_props": lambda_function_props,
            "schedule": schedule,
        }
        if alert_on_failure is not None:
            self._values["alert_on_failure"] = alert_on_failure
        if email_address is not None:
            self._values["email_address"] = email_address
        if lambda_target_props is not None:
            self._values["lambda_target_props"] = lambda_target_props

    @builtins.property
    def lambda_function_props(self) -> aws_cdk.aws_lambda.FunctionProps:
        '''
        :stability: experimental
        '''
        result = self._values.get("lambda_function_props")
        assert result is not None, "Required property 'lambda_function_props' is missing"
        return typing.cast(aws_cdk.aws_lambda.FunctionProps, result)

    @builtins.property
    def schedule(self) -> aws_cdk.aws_events.Schedule:
        '''
        :stability: experimental
        '''
        result = self._values.get("schedule")
        assert result is not None, "Required property 'schedule' is missing"
        return typing.cast(aws_cdk.aws_events.Schedule, result)

    @builtins.property
    def alert_on_failure(self) -> typing.Optional[builtins.bool]:
        '''(experimental) User can do this on their own or let pigeon handle it.

        Flipping this switch only turns on SNS alerting.
        Use emailAddress for an actual notification.

        :stability: experimental
        '''
        result = self._values.get("alert_on_failure")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def email_address(self) -> typing.Optional[builtins.str]:
        '''
        :stability: experimental
        '''
        result = self._values.get("email_address")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def lambda_target_props(
        self,
    ) -> typing.Optional[aws_cdk.aws_events_targets.LambdaFunctionProps]:
        '''(experimental) Let the user pass this in because timing is highly dependent on the schedule.

        Example:
        {
        deadLetterQueue: queue,
        maxEventAge: cdk.Duration.minutes(1),
        retryAttempts: 2,
        }

        :stability: experimental
        '''
        result = self._values.get("lambda_target_props")
        return typing.cast(typing.Optional[aws_cdk.aws_events_targets.LambdaFunctionProps], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PigeonProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Pigeon",
    "PigeonProps",
]

publication.publish()
