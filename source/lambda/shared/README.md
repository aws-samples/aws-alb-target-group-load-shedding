This folder contains the Lambda layer implementing the logic for ALB load shedding and restoring.

Unit tests are in the elb_load_monitor/test folder.

To build the Lambda layer and make it available for deployment by CDK, run build_lambda_layer.sh. The layer zip file will be created in  ${project.home}/cdk/resources/lambda_layer.
