run:
	sudo docker build -t xxxxx.dkr.ecr.us-east-1.amazonaws.com/pgbadger-executor-py:1.0 .
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin xxxxx.dkr.ecr.us-east-1.amazonaws.com/pgbadger-executor-py
	docker push xxxxx.dkr.ecr.us-east-1.amazonaws.com/pgbadger-executor-py:1.0

