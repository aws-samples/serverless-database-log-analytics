# Docker Image for PgBadger Lambda executor


## Update Makefile, Build the Image and push it to ecr
```
 make run
```

## Create Lambda using the Image from ecr
```
 set lambda timeout to 4 min
 env variables BADGER_OUTPUT_DIR to <efs mount dir>
 	       BADGER_OUTPUT_FILE to result.html
 Reserved concurrency to 1

 FileSystems:
  Mount efs filesystem
```
