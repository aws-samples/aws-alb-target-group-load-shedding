import pathlib

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import aws_cloudwatch, aws_events, aws_events_targets, aws_iam, aws_lambda
from aws_cdk import aws_lambda_event_sources, aws_sqs
from aws_cdk import core
from aws_cdk import core as cdk


class ALBMonitorStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        elb_target_group_arn = self.node.try_get_context('arn:aws:elasticloadbalancing:ap-south-1:661143522137:targetgroup/fkhp-prod-new-msite-tg-as1/d0daea7333f59341')

        if elb_target_group_arn is None:
            raise ValueError(
                'Must specify context parameter elbTargetGroupArn. Usage: cdk <COMMAND> -c elbTargetGroupArn ' +
                '<ELB_TARGET_GROUP_ARN>')

        elb_arn_parameter = core.CfnParameter(
            self, 'elbArn', type='String', description='ARN for ELB', default='arn:aws:elasticloadbalancing:ap-south-1:661143522137:loadbalancer/app/healthplus-flipkartcom-web/12ec89d83502ace9')
        elb_listener_arn_parameter = core.CfnParameter(
            self, 'elbListenerArn', type='String', description='ARN for ELB listener', default='arn:aws:elasticloadbalancing:ap-south-1:661143522137:listener/app/healthplus-flipkartcom-web/12ec89d83502ace9/a89018d096aa7035')
        elb_shed_percent_parameter = core.CfnParameter(
            self, 'elbShedPercent', type='Number', description='Percentage to shed expressed as an integer',
            min_value=0, max_value=90, default=5)
        max_elb_shed_percent_parameter = core.CfnParameter(
            self, 'maxElbShedPercent', type='Number', description='Maximum allowable load to shed from ELB',
            min_value=0, max_value=90, default=90)
        elb_restore_percent_parameter = core.CfnParameter(
            self, 'elbRestorePercent', type='Number', description='Percentage to restore expressed as an integer',
            min_value=0, max_value=90, default=5)
        shed_mesg_delay_sec_parameter = core.CfnParameter(
            self, 'shedMesgDelaySec', type='Number', description='Number of seconds to delay shed messages',
            min_value=60, max_value=300, default=60)
        restore_mesg_delay_sec_parameter = core.CfnParameter(
            self, 'restoreMesgDelaySec', type='Number', description='Number of seconds to delay restore messages',
            min_value=60, max_value=300, default=120)
        
        # These are the parameters for the CloudWatch Alarm
        cw_alarm_namespace = core.CfnParameter(
            self, 'cwAlarmNamespace', type='String', description='Namespace for alarm metric', default='AWS/ApplicationELB')
        cw_alarm_metric_name = core.CfnParameter(
            self, 'cwAlarmMetricName', type='String', description='Metric to use for alarm', default='TargetResponseTime')
        cw_alarm_metric_stat = core.CfnParameter(
            self, 'cwAlarmMetricStat', type='String', description='Statistic for the alarm e.g. sum, averge', default='average')
        cw_alarm_threshold = core.CfnParameter(
            self, 'cwAlarmThreshold', type='Number', description='Threshold for alarm', default=1)
        cw_alarm_periods = core.CfnParameter(
            self, 'cwAlarmPeriods', type='Number', description='Num of periods for alarm', default=2)



        # Queue used to monitor the ALB
        queue = aws_sqs.Queue(scope=self, id='alb_target_group_monitor_queue')

        # This policy allows create logs and put logs
        inline_policy_json_logs = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }

        #This policy allows sending messages to SQS on a single queue
        inline_policy_json_sqs ={
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Effect": "Allow",
                    "Action": [
                        'sqs:SendMessage',
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:ChangeMessageVisibility",
                        "sqs:GetQueueUrl"
                    ],
                    "Resource": queue.queue_arn
                }
            ]
        }


        alarm_lambda_execution_role = aws_iam.Role(
            self, 'ALBAlarmLambdaRole', 
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            description='Role assumed by ALB monitoring lambdas',
            managed_policies=[
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='cloud_watch_read',
                    managed_policy_arn='arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess'),
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='elb_full',
                    managed_policy_arn='arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess')
            ],
            inline_policies=[
                aws_iam.PolicyDocument.from_json(inline_policy_json_sqs),
                aws_iam.PolicyDocument.from_json(inline_policy_json_logs)]
        )


        # Code for Lambda function will will monitor load on the ELB
        layer_code = aws_lambda.AssetCode(path=str(pathlib.Path(
            __file__).parent.parent/'resources/lambda_layer/elb_load_monitor.zip'))

        # Lambda ZIP archive with additional code for ALB Monitoring
        elb_monitor_layer = aws_lambda.LayerVersion(
            self, 
            'ALBMonitorLayer', 
            description='ALBMonitoring Layer',
            layer_version_name='ALBMonitorLayer',
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_7, aws_lambda.Runtime.PYTHON_3_8
            ],
            code=layer_code)

        # todo1 need to check VPC and security groups
        # function needs access to elb and sqs api
        # if placed in vpc, need to add VPCEndpoint
        alarm_lambda_code = aws_lambda.AssetCode(path=str(pathlib.Path(
            __file__).parent.parent/'resources/lambda/alb_alarm_lambda_handler.zip'))

        self.alb_alarm_lambda = aws_lambda.Function(
            self, 
            'ALBAlarmLambda', 
            code=alarm_lambda_code, 
            handler='alb_alarm_lambda_handler.lambda_handler',
            function_name='ALBAlarmLambda',
            runtime=aws_lambda.Runtime.PYTHON_3_8, description='Lambda Handler for ALB Alarms',
            environment={
                'ELB_ARN': elb_arn_parameter.value_as_string,
                'ELB_LISTENER_ARN': elb_listener_arn_parameter.value_as_string,
                'SQS_QUEUE_URL': queue.queue_url,
                'ELB_SHED_PERCENT': elb_shed_percent_parameter.value_as_string,
                'MAX_ELB_SHED_PERCENT': max_elb_shed_percent_parameter.value_as_string,
                'ELB_RESTORE_PERCENT': elb_restore_percent_parameter.value_as_string,
                'SHED_MESG_DELAY_SEC': shed_mesg_delay_sec_parameter.value_as_string,
                'RESTORE_MESG_DELAY_SEC': restore_mesg_delay_sec_parameter.value_as_string
            },
            layers=[elb_monitor_layer], 
            memory_size=128,
            role=alarm_lambda_execution_role
        )
        
        # Create the Event Rule
        event_rule = aws_events.Rule(
            self, 'ALBTargetGroupAlarmEventRule', rule_name='ALBTargetGroupAlarmEventRule',
            description='EventBridge rule for ALB target')

        # Add the Lambda as the target of the Event Rule
        event_rule.add_target(
            aws_events_targets.LambdaFunction(self.alb_alarm_lambda))
        
        aws_lambda.CfnPermission(
            self,
            "eventRule",
            action="lambda:InvokeFunction",
            function_name=self.alb_alarm_lambda.function_arn,
            principal="events.amazonaws.com",
            source_arn= event_rule.rule_arn
        )

        # The role for the ALB Alarm Check Queue Lambda
        sqs_message_lambda_execution_role = aws_iam.Role(
            self, 'ALBSQSMessageLambdaRole', 
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            description='Role assumed by ALB SQS Message Lambda',
            managed_policies=[
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='cloud_watch_read2',
                    managed_policy_arn='arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess'),
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='elb_full2',
                    managed_policy_arn='arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess')
            ],
            inline_policies=[
                aws_iam.PolicyDocument.from_json(inline_policy_json_sqs),
                aws_iam.PolicyDocument.from_json(inline_policy_json_logs)]
        )

        # The code for the ALB Alarm Check Queue Lambda
        alb_sqs_message_lambda_code = aws_lambda.AssetCode(path=str(pathlib.Path(
            __file__).parent.parent/'resources/lambda/alb_alarm_check_lambda_handler.zip'))

        # Create the Lambda function from the code in alb_alarm_check_lambda_handler.zip
        alb_sqs_message_lambda = aws_lambda.Function(
            self, 
            'ALBSQSMessageLambda', 
            code=alb_sqs_message_lambda_code, 
            handler='alb_alarm_check_lambda_handler.lambda_handler',
            function_name='ALBSQSMessageLambda',
            runtime=aws_lambda.Runtime.PYTHON_3_8, 
            description='Lambda Handler for SQS Messages from ALB Monitor',
            layers=[elb_monitor_layer], 
            memory_size=128,
            role=sqs_message_lambda_execution_role
        )

        alb_sqs_message_lambda.add_event_source(
            aws_lambda_event_sources.SqsEventSource(queue))

        ##################################
        ## Set up the CloudWatch Alarm
        ##################################

        target_group_dimension = elb_target_group_arn[elb_target_group_arn.find(
            'targetgroup'):len(elb_target_group_arn)]

        # Fixing the parameter for cwAlarmMetricStat. At synth time, this value is $
        alarm_metric_stat = cw_alarm_metric_stat.value_as_string
        if cw_alarm_metric_stat.value_as_string.count("Token") > 0:
            alarm_metric_stat = 'average'
        
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

        event_rule.add_event_pattern(
            source=['aws.cloudwatch'], detail_type=['CloudWatch Alarm State Change'], resources=[cw_alarm.alarm_arn])
