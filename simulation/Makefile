# NS-3 Project Makefile
# P5 LoRa Simulation

# Configuration
NS3_DIR := $(HOME)/ns-allinone-3.43/ns-3.43
PROJECT_DIR := $(shell pwd)
SIM_DIR := src/simulations
RESULTS_DIR := results
SCRATCH_LINK := $(NS3_DIR)/scratch/p5-simulation

# Simulation names (add your .cc files here without extension)
SIMULATIONS := lora

# Default target
.PHONY: all
all: setup build

# Setup symlink
.PHONY: setup
setup:
	@echo "Setting up symlink to NS-3..."
	@mkdir -p $(SIM_DIR)
	@if [ ! -L $(SCRATCH_LINK) ]; then \
		ln -s $(PROJECT_DIR)/$(SIM_DIR) $(SCRATCH_LINK); \
		echo "✓ Symlink created"; \
	else \
		echo "✓ Symlink already exists"; \
	fi

# Build NS-3 with your simulations
.PHONY: build
build: setup
	@echo "Building NS-3 with simulations..."
	@cd $(NS3_DIR) && ./ns3 build
	@echo "✓ Build complete"

# Clean build
.PHONY: clean
clean:
	@echo "Cleaning NS-3 build..."
	@cd $(NS3_DIR) && ./ns3 clean
	@echo "✓ Clean complete"

# Rebuild everything
.PHONY: rebuild
rebuild: clean build

# Configure NS-3
.PHONY: configure
configure:
	@echo "Configuring NS-3..."
	@cd $(NS3_DIR) && ./ns3 configure --enable-examples --enable-tests
	@echo "✓ Configuration complete"

# Run specific simulation
.PHONY: run-%
run-%: build
	@echo "Running simulation: $*"
	@cd $(NS3_DIR) && ./ns3 run "p5-simulation/$*"

# Run with arguments
.PHONY: run-with-args
run-with-args: build
	@echo "Running: $(SIM) with args: $(ARGS)"
	@cd $(NS3_DIR) && ./ns3 run "p5-simulation/$(SIM) $(ARGS)"

# Example: make run-with-args SIM=lora-range-test ARGS="--nDevices=10 --distance=1500"

# Run all simulations
.PHONY: run-all
run-all: build
	@for sim in $(SIMULATIONS); do \
		echo "Running $$sim..."; \
		cd $(NS3_DIR) && ./ns3 run "p5-simulation/$$sim"; \
	done

# Create results directory
.PHONY: results-dir
results-dir:
	@mkdir -p $(RESULTS_DIR)

# Run experiments with different parameters
.PHONY: experiment
experiment: build results-dir
	@echo "Running experiments..."
	@for dist in 500 1000 1500 2000; do \
		echo "Testing distance: $$dist m"; \
		cd $(NS3_DIR) && ./ns3 run "p5-simulation/lora-range-test --distance=$$dist" \
			> $(PROJECT_DIR)/$(RESULTS_DIR)/range_$${dist}m.txt; \
	done
	@echo "✓ Experiments complete. Results in $(RESULTS_DIR)/"

# List available simulations
.PHONY: list
list:
	@echo "Available simulations:"
	@cd $(SIM_DIR) && ls -1 *.cc 2>/dev/null | sed 's/.cc$$/  - /' || echo "  (none found)"

# Show simulation paths
.PHONY: info
info:
	@echo "Project Configuration:"
	@echo "  NS-3 Dir:      $(NS3_DIR)"
	@echo "  Project Dir:   $(PROJECT_DIR)"
	@echo "  Simulations:   $(SIM_DIR)"
	@echo "  Results:       $(RESULTS_DIR)"
	@echo "  Symlink:       $(SCRATCH_LINK)"
	@echo ""
	@echo "Available simulations:"
	@$(MAKE) list

# Remove symlink
.PHONY: unlink
unlink:
	@echo "Removing symlink..."
	@rm -f $(SCRATCH_LINK)
	@echo "✓ Symlink removed"

# Clean project results
.PHONY: clean-results
clean-results:
	@echo "Cleaning results..."
	@rm -rf $(RESULTS_DIR)/*
	@echo "✓ Results cleaned"

# Help target
.PHONY: help
help:
	@echo "P5 LoRa Simulation - Available targets:"
	@echo ""
	@echo "  make setup          - Create symlink to NS-3"
	@echo "  make build          - Build NS-3 with simulations"
	@echo "  make clean          - Clean NS-3 build"
	@echo "  make rebuild        - Clean and rebuild"
	@echo "  make configure      - Configure NS-3"
	@echo ""
	@echo "  make run-<name>     - Run specific simulation"
	@echo "  make run-all        - Run all simulations"
	@echo "  make experiment     - Run parameter sweep experiments"
	@echo ""
	@echo "  make list           - List available simulations"
	@echo "  make info           - Show project configuration"
	@echo "  make help           - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make run-lora-range-test"
	@echo "  make run-with-args SIM=lora-range-test ARGS=\"--nDevices=10\""
	@echo "  make experiment"
