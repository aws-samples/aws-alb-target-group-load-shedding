import pathlib

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import aws_cloudwatch, aws_events, aws_events_targets, aws_iam, aws_lambda
from aws_cdk import aws_lambda_event_sources, aws_sqs
from aws_cdk import core
from aws_cdk import core as cdk

class ALBCloudWatchStack(cdk.Stack):
    
    def __init__(self, scope: cdk.Construct, construct_id: str,  **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        elb_target_group_arn = self.node.try_get_context('elbTargetGroupArn')

        if elb_target_group_arn is None:
            raise ValueError(
                'Must specify context parameter elbTargetGroupArn. Usage: cdk <COMMAND> -c elbTargetGroupArn ' +
                '<ELB_TARGET_GROUP_ARN>')

        alb_sqs_alarm_lambda = self.node.try_get_context('')

        target_group_dimension = elb_target_group_arn[elb_target_group_arn.find(
            'targetgroup'):len(elb_target_group_arn)]

        cw_alarm_lambda_arn = core.CfnParameter(
            self, 'cwAlarmLambdaArn', type='String', description='ARN for Lambda to fire when in Alarm')
        cw_alarm_namespace = core.CfnParameter(
            self, 'cwAlarmNamespace', type='String', description='Namespace for alarm metric', default='AWS/ApplicationELB')
        cw_alarm_metric_name = core.CfnParameter(
            self, 'cwAlarmMetricName', type='String', description='Metric to use for alarm', default='RequestCountPerTarget')
        cw_alarm_metric_stat = core.CfnParameter(
            self, 'cwAlarmMetricStat', type='String', description='Statistic for the alarm e.g. sum, averge', default='sum')
        cw_alarm_threshold = core.CfnParameter(
            self, 'cwAlarmThreshold', type='Number', description='Threshold for alarm', default=500)
        cw_alarm_periods = core.CfnParameter(
            self, 'cwAlarmPeriods', type='Number', description='Num of periods for alarm', default=3)

        # Fixing the parameter for cwAlarmMetricStat. At synth time, this value is $
        alarm_metric_stat = cw_alarm_metric_stat.value_as_string
        if cw_alarm_metric_stat.value_as_string.count("Token") > 0:
            alarm_metric_stat = 'sum'
        
        # The evaluation period for the alarm will be 60s/1m.
        request_count_per_target_metric = aws_cloudwatch.Metric(
            namespace=cw_alarm_namespace.value_as_string,
            metric_name=cw_alarm_metric_name.value_as_string,
            dimensions={
                "TargetGroup": target_group_dimension
            },
            statistic=alarm_metric_stat,
            period=cdk.Duration.minutes(1)
        )

        cw_alarm = aws_cloudwatch.Alarm(
            self, 'ALBTargetGroupAlarm', 
            alarm_name='ALBTargetGroupAlarm',
            alarm_description='Alarm for RequestCountPerTarget',
            metric=request_count_per_target_metric, 
            threshold=cw_alarm_threshold.value_as_number,
            evaluation_periods=cw_alarm_periods.value_as_number,
            comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD)

        event_rule = aws_events.Rule(
            self, 'ALBTargetGroupAlarmEventRule', rule_name='ALBTargetGroupAlarmEventRule',
            description='EventBridge rule for ALB target')

        event_rule.add_event_pattern(
            source=['aws.cloudwatch'], detail_type=['CloudWatch Alarm State Change'], resources=[cw_alarm.alarm_arn])


        alb_sqs_alarm_lambda = aws_lambda.Function.from_function_arn(
            self,
            id="alb_sqs_alarm_lambda",
            function_arn=cw_alarm_lambda_arn.value_as_string)

        event_rule.add_target(
            aws_events_targets.LambdaFunction(alb_sqs_alarm_lambda))

        aws_lambda.CfnPermission(
            self,
            "eventRule",
            action="lambda:InvokeFunction",
            function_name=cw_alarm_lambda_arn.value_as_string,
            principal="apigateway.amazonaws.com",
            source_arn= event_rule.rule_arn
        )

