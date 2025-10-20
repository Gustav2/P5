# NS-3 Project Makefile
# P5 LoRa Simulation

# Configuration
NS3_DIR := $(HOME)/ns-allinone-3.43/ns-3.43
PROJECT_DIR := $(shell pwd)
SIM_DIR := src/simulations
RESULTS_DIR := results
SCRATCH_LINK := $(NS3_DIR)/scratch/p5-simulation

# Build NS-3 arguments from variables
NS3_ARGS :=
ifdef NDEVICES
    NS3_ARGS += --nDevices=$(NDEVICES)
endif
ifdef TIME
    NS3_ARGS += --time=$(TIME)
endif
ifdef DISTANCE
    NS3_ARGS += --distance=$(DISTANCE)
endif

# Default target
.PHONY: all
all: setup build

# Setup symlink
.PHONY: setup
setup:
	@mkdir -p $(SIM_DIR)
	@if [ ! -L $(SCRATCH_LINK) ]; then \
		ln -s $(PROJECT_DIR)/$(SIM_DIR) $(SCRATCH_LINK); \
		echo "✓ Symlink created"; \
	else \
		echo "✓ Symlink already exists"; \
	fi

# Build NS-3
.PHONY: build
build: setup
	@echo "Building NS-3..."
	@cd $(NS3_DIR) && ./ns3 build
	@echo "✓ Build complete"

# Clean build
.PHONY: clean
clean:
	@cd $(NS3_DIR) && ./ns3 clean
	@echo "✓ Clean complete"

# Rebuild
.PHONY: rebuild
rebuild: clean build

# Configure NS-3
.PHONY: configure
configure:
	@cd $(NS3_DIR) && ./ns3 configure --enable-examples --enable-tests
	@echo "✓ Configuration complete"

# Run simulation
# Usage: make run lora NDEVICES=10 TIME=100
.PHONY: run
run: build
	@if [ "$(filter-out run,$(MAKECMDGOALS))" = "" ]; then \
		echo "Error: No simulation specified"; \
		echo "Usage: make run <simulation> [NDEVICES=N] [TIME=T] [DISTANCE=D]"; \
		echo "Example: make run lora NDEVICES=10 TIME=100"; \
		exit 1; \
	fi
	@SIM_NAME=$(filter-out run,$(MAKECMDGOALS)); \
	echo "Running: p5-simulation/$$SIM_NAME $(NS3_ARGS)"; \
	cd $(NS3_DIR) && ./ns3 run "p5-simulation/$$SIM_NAME $(NS3_ARGS)"

# Run with verbose logging
.PHONY: run-verbose
run-verbose: build
	@SIM_NAME=$(filter-out run-verbose,$(MAKECMDGOALS)); \
	if [ -z "$$SIM_NAME" ]; then \
		echo "Error: No simulation specified"; \
		exit 1; \
	fi; \
	echo "Running with verbose logging: p5-simulation/$$SIM_NAME"; \
	cd $(NS3_DIR) && NS_LOG="*=info" ./ns3 run "p5-simulation/$$SIM_NAME $(NS3_ARGS)"

# Run and save output
.PHONY: run-save
run-save: build
	@mkdir -p $(RESULTS_DIR)
	@SIM_NAME=$(filter-out run-save,$(MAKECMDGOALS)); \
	if [ -z "$$SIM_NAME" ]; then \
		echo "Error: No simulation specified"; \
		exit 1; \
	fi; \
	TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	OUTPUT_FILE=$(RESULTS_DIR)/$${SIM_NAME}_$$TIMESTAMP.txt; \
	echo "Running and saving to: $$OUTPUT_FILE"; \
	cd $(NS3_DIR) && ./ns3 run "p5-simulation/$$SIM_NAME $(NS3_ARGS)" > $(PROJECT_DIR)/$$OUTPUT_FILE; \
	echo "✓ Output saved to $$OUTPUT_FILE"

# Run experiments
.PHONY: experiment
experiment: build
	@mkdir -p $(RESULTS_DIR)
	@echo "Running experiments..."
	@for devices in 5 10 15 20; do \
		for dist in 500 1000 1500 2000; do \
			echo "Testing: $$devices devices, $$dist m radius"; \
			cd $(NS3_DIR) && ./ns3 run "p5-simulation/lora --nDevices=$$devices --distance=$$dist" \
				> $(PROJECT_DIR)/$(RESULTS_DIR)/lora_d$${devices}_r$${dist}m.txt; \
		done; \
	done
	@echo "✓ Experiments complete. Results in $(RESULTS_DIR)/"

# List available simulations
.PHONY: list
list:
	@echo "Available simulations:"
	@cd $(SIM_DIR) 2>/dev/null && ls -1 *.cc | sed 's/.cc$$/  - /' || echo "  (none found)"

# Show project info
.PHONY: info
info:
	@echo "Project Configuration:"
	@echo "  NS-3 Dir:      $(NS3_DIR)"
	@echo "  Project Dir:   $(PROJECT_DIR)"
	@echo "  Simulations:   $(SIM_DIR)"
	@echo "  Results:       $(RESULTS_DIR)"
	@echo "  Symlink:       $(SCRATCH_LINK)"
	@echo ""
	@$(MAKE) -s list

# Remove symlink
.PHONY: unlink
unlink:
	@rm -f $(SCRATCH_LINK)
	@echo "✓ Symlink removed"

# Clean results
.PHONY: clean-results
clean-results:
	@rm -rf $(RESULTS_DIR)/*
	@echo "✓ Results cleaned"

# Help
.PHONY: help
help:
	@echo "P5 LoRa Simulation - Available targets:"
	@echo ""
	@echo "Building:"
	@echo "  make setup          - Create symlink to NS-3"
	@echo "  make build          - Build NS-3"
	@echo "  make clean          - Clean build"
	@echo "  make rebuild        - Clean and rebuild"
	@echo ""
	@echo "Running:"
	@echo "  make run <name>                    - Run simulation"
	@echo "  make run <name> NDEVICES=10        - Run with number of devices"
	@echo "  make run <name> TIME=100           - Run with simulation time"
	@echo "  make run <name> DISTANCE=1500      - Run with distance"
	@echo "  make run-verbose <name> [params]   - Run with logging"
	@echo "  make run-save <name> [params]      - Save output to file"
	@echo "  make experiment                    - Run parameter sweep"
	@echo ""
	@echo "Utilities:"
	@echo "  make list           - List available simulations"
	@echo "  make info           - Show configuration"
	@echo "  make clean-results  - Clean results"
	@echo ""
	@echo "Examples:"
	@echo "  make run lora"
	@echo "  make run lora NDEVICES=10"
	@echo "  make run lora NDEVICES=20 TIME=200"
	@echo "  make run lora NDEVICES=15 TIME=100 DISTANCE=2000"
	@echo "  make run-save lora NDEVICES=10"

# Catch-all to prevent "No rule to make target" errors
%:
	@:
