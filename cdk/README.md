
# Application Load Balancer Target Group Load Shedding.

This is the Python CDK for the ALB Target Group Load Shedding project. Please consult the AWS CDK documentation on how to configure the CDK.

Make sure you update the CDK and also install the appropriate Python libraries by running
    
    npm install -g aws-cdk
    python -m pip install -r requirements.txt


The project contains 2 Stacks:
1. *ALBMonitorStack* contains 2 Lambda functions, a SQS queue, and appropriate IAM roles. The stack encapsulates logic to shed and restore load for on an ALB Target Group.
2. *ALBCloudWatchStack* contains an sample CloudWatch Alarm and an EventBridge rule. The EventBridge rule routes CloudWatch Alarm change events to the appropriate Lambda function in the ALBMonitorStack

If you update the Lambda functions or code in the Lambda layer, please run:

    ${project.home}/source/build_lambda_functions.sh
or

    ${project.home}/source/shared/build_lambda_layer.sh

The scripts will update the Lambda function zip file or Lambda layer zip file respectively.

To synthesize the CloudFormation templates:

    cdk synth -c elbTargetGroupArn="arn:aws:elasticloadbalancing:SOME_REGION:SOME_ACCOUNT_NUM:targetgroup/AppServerATG/090a4ba28ada9d48"

Replace the *elbTargetGroupArn* context parameter value with the ARN for your desired Target Group. The stack uses the elbTargetGroupArn parameter value to generate the correct CF template. As a prerequisite, you must have Application Load Balancers with appropriate Target Groups in your AWS environment.

To deploy the stacks:

    cdk deploy ALBMonitorStack -c elbTargetGroupArn="arn:aws:elasticloadbalancing:SOME_REGION:SOME_ACCOUNT_NUM:targetgroup/AppServerATG/090a4ba28ada9d48" --parameters elbArn="arn:aws:elasticloadbalancing:SOME_REGION:SOME_ACCOUNT_NUM:loadbalancer/app/AgentPortalALB/bb6bb42b08f94c0b" --parameters elbListenerArn="arn:aws:elasticloadbalancing:SOME_REGION:SOME_ACCOUNT_NUM:listener/app/AgentPortalALB/bb6bb42b08f94c0b/b3784a6b090b3696"

    cdk deploy ALBCloudWatchStack -c elbTargetGroupArn="arn:aws:elasticloadbalancing:SOME_REGION:SOME_ACCOUNT_NUM:targetgroup/AppServerATG/090a4ba28ada9d48" --parameters cwAlarmThreshold=500

Provide the appropriate parameter values. The follow parameters are required:

    elbArn - ARN for the Application Load Balancer (ALB) to monitor
    elbListenerARN - ARN for the ALB Listener to update for shedding/restoring

The following parameters are optional:

    cwAlarmNamespace - The namespace for the CloudWatch (CW) metric (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/viewing_metrics_with_cloudwatch.html). Default: AWS/ApplicationELB
    cwAlarmMetricName - The name of the CW metric. Default: RequestCountPerTarget
    cwAlarmMetricStatistic - Function to use for aggregating the statistic. Default: Average
    cwAlarmThreshold - Threshold value that triggers an alarm for the metric. Default: 500
    cwAlarmPeriods - The evaluation period for the alarm. Default: 3.
