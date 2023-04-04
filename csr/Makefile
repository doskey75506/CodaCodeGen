include ../env.mk

BLOCK_NAME = csr
STUDIO_CMD = codasip_cmdline_$(STUDIO_VERSION)
#STUDIO_CMD = codasip_cmdline_10.0.0-302

VSRCS =	$(RTL_DIR)/csr_type_pkg.sv                    \
		$(wildcard $(RTL_DIR)/ccu_core_main_csr_*.sv) \
		$(wildcard $(RTL_DIR)/common/*.sv)

# Genus constraints file for synthesis
GENUS_SDC = genus/constraints.sdc

# Top-level module name
TOP_MODULE = csr_core_main_csr_t

all: rtl

.PHONY: help
help:
	@echo "Please select a task (gen, rtl, full_rtl, clean)"


.PHONY: gen
gen:
	@echo "  Running CSR_BANK generation..."
	@./script/gen_code.sh


.PHONY: rtl
rtl: clean
	@echo "  RTL Only Build..."
	@$(STUDIO_CMDLINE) $(STUDIO_ARGS)


.PHONY: full_rtl
full_rtl:
	@echo "  Full RTL Build..."
	@$(STUDIO_CMDLINE) -m codasip.build rtl --codal-option "general.verbosity=3"


.PHONY: lint-verilator
lint-verilator:
	@echo "  RTL Lint Verilator..."
	@$(VERILATOR) $(VERILATOR_ARGS) $(VSRCS)


.PHONY: lint-alint
lint-alint:
	@echo "  RTL Lint Alint..."
	@CSR_RTL_SVERILOG_ROOT="work/hdk/rtl/sverilog" $(ALINT)     \
		$(ALINT_ARGS)                                           \
		-project_name $(PROJ_NAME)                              \
		$(VSRCS)


.PHONY: lint-spyglass
lint-spyglass:
	@echo "  RTL Lint Spyglass..."
	@$(SPYGLASS_PY) $(SPYGLASS_ARGS) --top $(TOP_MODULE)


.PHONY: syn-genus
syn-genus:
	@echo "  RTL Synthesis Genus..."
	@$(GENUS_PY) $(GENUS_ARGS) --top $(TOP_MODULE) --sdc $(GENUS_SDC)


.PHONY: clean
clean:
	@echo "  Deleting work/..."
	@rm -rf ./work/
