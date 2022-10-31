SMART_BINARY_DIR = ${CURDIR}/bin

include Makefile.common
.PHONY: all smartctl
all: smartctl

prepare:
	@mkdir -p $(SMART_HOME)
	@rm -rf $(SMART_HOME)/resource
	@cp -r $(CURDIR)/resource $(SMART_HOME)/

smartctl: prepare
	@echo "start to build smartctl"
	$(GOBUILD) -o $(SMART_BINARY_DIR)/smartctl cmd/smartctl/*.go
	@echo "build smartctl successfully"
