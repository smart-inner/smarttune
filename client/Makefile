include Makefile.common
.PHONY: all smartctl
all: smartctl

smartctl:
	@echo "start to build smartctl"
	$(GOBUILD) -o bin/smartctl cmd/smartctl/*.go
	@echo "build smartctl successfully"