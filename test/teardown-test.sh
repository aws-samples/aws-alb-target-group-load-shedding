#!/bin/bash
# Teardown test infrastructure

set -e

REGION=${AWS_REGION:-us-east-1}

echo "🗑️  Tearing down test infrastructure in $REGION..."

# Get Primary Target Group ARN from prerequisites stack
PTG_ARN=$(aws cloudformation describe-stacks \
  --stack-name ALBTestPrerequisites \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`PrimaryTargetGroupArn`].OutputValue' \
  --output text 2>/dev/null)

# Delete ALBMonitorStack
if [ -n "$PTG_ARN" ]; then
  echo "Deleting ALBMonitorStack..."
  cd ../cdk
  cdk destroy ALBMonitorStack \
    -c elbTargetGroupArn="$PTG_ARN" \
    --force \
    --region $REGION 2>/dev/null || echo "ALBMonitorStack not found or already deleted"
  cd ../test
fi

# Delete ALBTestPrerequisites
echo "Deleting ALBTestPrerequisites..."
aws cloudformation delete-stack \
  --stack-name ALBTestPrerequisites \
  --region $REGION

echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
  --stack-name ALBTestPrerequisites \
  --region $REGION

echo "✅ All test resources deleted"
