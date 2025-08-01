include etc/environment.sh

# dependencies
layer: layer.build layer.package layer.deploy
layer.build:
	sam build -t ${LAYER_TEMPLATE} --parameter-overrides ${LAYER_PARAMS} --build-dir build --manifest layer/requirements.txt --use-container
layer.package:
	sam package -t build/template.yaml --region ${REGION} --output-template-file ${LAYER_OUTPUT} --s3-bucket ${BUCKET} --s3-prefix ${LAYER_STACK}
layer.deploy:
	sam deploy -t ${LAYER_OUTPUT} --region ${REGION} --stack-name ${LAYER_STACK} --parameter-overrides ${LAYER_PARAMS} --capabilities CAPABILITY_NAMED_IAM

# api gateway
apigw: apigw.package apigw.deploy
apigw.package:
	# 替换template.yaml中的区域变量
	sed -i "s|arn:aws:lambda:ap-southeast-1:|arn:aws:lambda:${REGION}:|g" iac/template.yaml
	echo "已将template.yaml中的区域从ap-southeast-1更新为${REGION}"

	# 设置AWS CLI默认区域
	export AWS_DEFAULT_REGION=${REGION}
	aws configure set region ${REGION} --profile ${PROFILE}
	echo "AWS CLI区域已设置为: ${REGION}"
	
	sam package -t ${APIGW_TEMPLATE} --output-template-file ${APIGW_OUTPUT} --s3-bucket ${BUCKET} --s3-prefix ${APIGW_STACK}
apigw.deploy:
	sam deploy -t ${APIGW_OUTPUT} --region ${REGION} --stack-name ${APIGW_STACK} --parameter-overrides ${APIGW_PARAMS} --capabilities CAPABILITY_NAMED_IAM
apigw.delete:
	sam delete --stack-name ${APIGW_STACK}
