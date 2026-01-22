# Application Load Balancer Target Group Load Shedding.

This Github repository is created to provide the sample source for the AWS blog post- Target Group Load Shedding for Application Load Balancer.

In this blog post we discuss the Application Load Balancer Target Group Load Shedding (ALB TGLS) Solution, when it's appropriate, and how to deploy the solution into your own AWS Account using the AWS Cloud Development Kit template.


## Prerequisites

- Python 3.13 or later
- AWS CDK installed and configured
- Application Load Balancer with weighted target group routing
# Architecture

![ALB TGLS Simplified - Numbered](https://user-images.githubusercontent.com/33617809/124167984-278ef180-da6a-11eb-88b0-3e2f30abafbc.png)

1. An Amazon CloudWatch Alarm configured to breach based on specific use case requirements experiences a change in state. This state change is picked up by Amazon EventBridge
2. Amazon EventBridge invokes an ALB TGLS Lambda function
3. The Lambda function checks the current state of the environment. If the state of the Primary Target Group (PTG) is either OverLoaded or UnderLoaded, the appropriate Load Shedding or Restore actions are taken. For Load Shedding actions, an incremental percentage of traffic is Shed from the PTG to the Shedding Target Group (STG). For Load Restores, an increment of the shedding action is reversed from the STG to the PTG. After Load Shedding and Restore actions, a message is sent to Amazon SQS with a visibility timeout for further incremental action until the PTG environment stabilizes
4. The Amazon SQS queue delivers a message to the ALB TGLS Lambda function after a delay period. The ALB TGLS Lambda function evaluates the message to either perform another round of Load Shedding or Load Restore as appropriate
5. Points 3 and 4 above are repeated until the ALB TGLS Lambda Solution has restored 100% of the load back to the PTG environment, and finds the environment to be in a steady state. When the environment reaches a steady state no action is taken and the environment is considered healthy until the CloudWatch Alarm state change occurs again

See [/cdk](https://github.com/aws-samples/aws-alb-target-group-load-shedding/tree/main/cdk) for steps to deploying the ALB TGLS Solution with the ALBMonitor CDK stack.
