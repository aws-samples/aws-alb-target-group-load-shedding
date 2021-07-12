#!/bin/bash
zip alb_alarm_lambda_handler.zip alb_alarm_lambda_handler.py
zip alb_alarm_check_lambda_handler.zip alb_alarm_check_lambda_handler.py
mv alb_alarm_lambda_handler.zip ../../cdk/resources/lambda/
mv alb_alarm_check_lambda_handler.zip ../../cdk/resources/lambda/