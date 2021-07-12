#!/bin/bash
rm -rf build
python3 -m setup build
cd build
mv lib python
zip -r elb_load_monitor.zip python
mv elb_load_monitor.zip ../../../../cdk/resources/lambda_layer/
