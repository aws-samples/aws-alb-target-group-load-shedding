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

        elb_arn_parameter = core.CfnParameter(
            self, 'elbArn', type='String', description='ARN for ELB')
        elb_listener_arn_parameter = core.CfnParameter(
            self, 'elbListenerArn', type='String', description='ARN for ELB listener')
        elb_shed_percent_parameter = core.CfnParameter(
            self, 'elbShedPercent', type='Number', description='Percentage to shed expressed as an integer',
            min_value=0, max_value=100, default=5)
        max_elb_shed_percent_parameter = core.CfnParameter(
            self, 'maxElbShedPercent', type='Number', description='Maximum allowable load to shed from ELB',
            min_value=0, max_value=100, default=100)
        elb_restore_percent_parameter = core.CfnParameter(
            self, 'elbRestorePercent', type='Number', description='Percentage to restore expressed as an integer',
            min_value=0, max_value=100, default=5)
        shed_mesg_delay_sec_parameter = core.CfnParameter(
            self, 'shedMesgDelaySec', type='Number', description='Number of seconds to delay shed messages',
            min_value=60, max_value=300, default=60)
        restore_mesg_delay_sec_parameter = core.CfnParameter(
            self, 'restoreMesgDelaySec', type='Number', description='Number of seconds to delay restore messages',
            min_value=60, max_value=300, default=120)

        # Queue used to monitor the ALB
        queue = aws_sqs.Queue(scope=self, id='alb_target_group_monitor_queue')

        # This policy allows sending messages to SQS.
        send_sqs_json = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 'sqs:SendMessage',
                    'Resource': queue.queue_arn
                }
            ]
        }

        # Create the policy document for the Queue from the JSON
        send_sqs_policy_document = aws_iam.PolicyDocument.from_json(
            send_sqs_json)

        # todo need to refine permissions
        # do not need full SQS access. Only require LambdaSQSQueueExecuteRole + queue send permissions
        lambda_execution_role = aws_iam.Role(
            self, 'ALB_Lambda_Role', 
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            description='Role assumed by ALB monitoring lambdas',
            managed_policies=[
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='lambda_execute',
                    managed_policy_arn='arn:aws:iam::aws:policy/AWSLambdaExecute'),
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='lambda_sqs_execute',
                    managed_policy_arn='arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole'),
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='cloud_watch_read',
                    managed_policy_arn='arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess'),
                aws_iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='elb_read',
                    managed_policy_arn='arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess')
            ],
            inline_policies=[send_sqs_policy_document]
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
            role=lambda_execution_role
        )

        # The code for the ALB Alarm Check Queue Lambda
        alb_sqs_message_lambda_code = aws_lambda.AssetCode(path=str(pathlib.Path(
            __file__).parent.parent/'resources/lambda/alb_alarm_check_lambda_handler.zip'))

        # Create the Lambda function from the 
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
            role=lambda_execution_role
        )

        alb_sqs_message_lambda.add_event_source(
            aws_lambda_event_sources.SqsEventSource(queue))

        cdk.CfnOutput(
            self, 'cwAlarmLambdaArn', value=self.alb_alarm_lambda.function_arn)
    
    @property
    def alarm_lambda(self) -> aws_lambda.IFunction:
        return self.alb_alarm_lambda


