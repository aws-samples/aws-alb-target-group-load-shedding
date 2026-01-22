
# Application Load Balancer Target Group Load Shedding.

This is the Python CDK for the ALB Target Group Load Shedding project. Please consult the AWS CDK documentation on how to configure the CDK.

\n**Requirements:** Python 3.13 or later

As a prerequisite, you must:
1. Have Application Load Balancers with appropriate Target Groups in your AWS environment. For guidance follow [these steps](https://aws.amazon.com/premiumsupport/knowledge-center/elb-make-weighted-target-groups-for-alb/).
2. ALB listener weighted rules to be configured with 100 weight to Primary Target Group and 0 weight to Shedding Target Group.

Make sure you update the CDK and also install the appropriate Python libraries by running (the below have been tested using [AWS Cloud9](https://aws.amazon.com/cloud9/))
    
    npm install -g aws-cdk
    pip install --upgrade pip
    python3 -m pip install -r requirements.txt

To prepare your environment for CDK usage, run

    cdk bootstrap -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN"

To synthesize the CloudFormation template:

    cdk synth -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN"

Replace the *elbTargetGroupArn* context parameter value with the ARN for your desired Target Group. The stack uses the elbTargetGroupArn parameter value to generate the correct CF template.

To deploy the ALBMonitorStack:

    cdk deploy ALBMonitorStack -c elbTargetGroupArn="REPLACE_WITH_YOUR_ELBTARGETGROUP_ARN" --parameters elbArn="REPLACE_WITH_YOUR_ELB_ARN" --parameters elbListenerArn="REPLACE_WITH_YOUR_ELBLISTENER_ARN"

Provide the appropriate parameter values. The follow parameters are required:

- elbArn - ARN for the Application Load Balancer (ALB) to monitor
- elbTargetGroupArn - ARN for the ALB's Primary Target Group
- elbListenerARN - ARN for the ALB Listener to update for shedding/restoring

The following parameters are optional:
- elbShedPercent - Percentage of traffic to shed expressed as an integer. Default: 5
- elbRestorePercent - Percentage of traffic to restore expressed as an integer. Default: 5
- maxElbShedPercent - Maximum allowable load to shed from Primary Target Group to Shedding Target Group. Default: 100
- shedMesgDelaySec - Time delay in seconds between Shed intervals expressed as an integer. Default: 60
- restoreMesgDelaySec - Time delay in seconds between Restore intervals. Default: 120
- cwAlarmNamespace - The namespace for the CloudWatch (CW) metric (https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/viewing_metrics_with_cloudwatch.html). Default: AWS/ApplicationELB
- cwAlarmMetricName - The name of the CW metric. Default: RequestCountPerTarget
- cwAlarmMetricStat - Function to use for aggregating the statistic. Can be one of the following: - "Minimum" | "min" - "Maximum" | "max" - "Average" | "avg" - "Sum" | "sum" - "SampleCount | "n" - "pNN.NN" Default: sum
- cwAlarmThreshold - Threshold value that triggers an alarm for the metric. Default: 500
- cwAlarmPeriods - The evaluation period for the alarm. Default: 3.


