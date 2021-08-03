
# Application Load Balancer Target Group Load Shedding.

This is the Python CDK for the ALB Target Group Load Shedding project. Please consult the AWS CDK documentation on how to configure the CDK.

Make sure you update the CDK and also install the appropriate Python libraries by running
    
    npm install -g aws-cdk
    python3 -m pip install -r requirements.txt


The project contains 2 Stacks:
1. *ALBMonitorStack* contains 2 Lambda functions, a SQS queue, and appropriate IAM roles. The stack encapsulates logic to shed and restore load for on an ALB Target Group.
2. *ALBCloudWatchStack* contains an sample CloudWatch Alarm and an EventBridge rule. The EventBridge rule routes CloudWatch Alarm change events to the appropriate Lambda function in the ALBMonitorStack

If you update the Lambda functions or code in the Lambda layer, please run:

    ${project.home}/source/build_lambda_functions.sh
or

    ${project.home}/source/shared/build_lambda_layer.sh

The scripts will update the Lambda function zip file or Lambda layer zip file respectively.

To prepare your environment for CDK usage, run 

    cdk bootstrap -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN"

To synthesize the CloudFormation templates:

    cdk synth -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN"

Replace the *elbTargetGroupArn* context parameter value with the ARN for your desired Target Group. The stack uses the elbTargetGroupArn parameter value to generate the correct CF template. As a prerequisite, you must have Application Load Balancers with appropriate Target Groups in your AWS environment.

To deploy the ALBMonitorStack:

    cdk deploy ALBMonitorStack -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN" --parameters elbArn="REPLACE_WITH_YOUR_ELB_ARN" --parameters elbListenerArn="REPLACE_WITH_YOUR_ELBLISTENER_ARN"

Note: Deployment of ALBMonitorStack will output the ARN of the Lambda provide to ALBCloudWatchStack.

Provide the appropriate parameter values. The follow parameters are required:

    elbArn - ARN for the Application Load Balancer (ALB) to monitor
    elbListenerARN - ARN for the ALB Listener to update for shedding/restoring

The following parameters are optional:
    elbShedPercent - Percentage to shed expressed as an integer. Default: 5
    maxElbShedPercent - aximum allowable load to shed from ELB. Default: 100
    elbRestorePercent - Percentage to restore expressed as an integer. Default: 5
    shedMesgDelaySec - Number of seconds to delay shed messages. Default: 60
    restoreMesgDelaySec - Number of seconds to delay restore messages. Default: 120

To deploy the ALBCloudWatchStack:

    cdk deploy ALBCloudWatchStack -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN" --parameters cwAlarmLambdaArn="REPLACE_WITH_YOUR_LAMBDA_ARN" --

Provide the appropriate parameter values. The follow parameters are required:
    cwAlarmLambdaArn - ARN for Lambda to fire when in Alarm state. 

The following parameters are optional:
    cwAlarmNamespace - The namespace for the CloudWatch (CW) metric (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/viewing_metrics_with_cloudwatch.html). Default: AWS/ApplicationELB
    cwAlarmMetricName - The name of the CW metric. Default: RequestCountPerTarget
    cwAlarmMetricStat - Function to use for aggregating the statistic. Default: Sum
    cwAlarmThreshold - Threshold value that triggers an alarm for the metric. Default: 500
    cwAlarmPeriods - The evaluation period for the alarm. Default: 3.


