include Makefile.common
.PHONY: all smart-ctl
all: smart-ctl

smart-ctl:
	@echo "start to build smart-ctl"
	$(GOBUILD) -o bin/smartctl cmd/smartctl/*.go
	@echo "build smart-ctl successfully"