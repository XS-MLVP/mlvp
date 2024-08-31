#Makefile for Adder

export SIMULATOR = verilator
export TRACE := fst
export PROJECT := Adder
export TARGET := UT_Adder
export VERBOSE := OFF
export EXAMPLE := ON
export TLANG := python
export SIMULATOR_FLAGS := 
export CFLAGS := 
export COVERAGE := ON

all: release 

compile:
	cmake . -Bbuild -DSIMULATOR=$(SIMULATOR) -DTRACE=$(TRACE) -DPROJECT=$(PROJECT) \
		-DSIMULATOR_FLAGS=$(SIMULATOR_FLAGS) -DCFLAGS=$(CFLAGS) -DCOVERAGE=$(COVERAGE)
	cmake --build build --config Debug --parallel `nproc`

release: compile
	@cp -r build/${TARGET} .
	@cp dut_base.hpp ${TARGET}/dut_base.hpp
	@make -f mk/${TLANG}.mk

ifeq ($(VERBOSE), OFF) # if VERBOSE is OFF

ifeq ($(COVERAGE), OFF)
	@rm Makefile
	@rm *.v *.sv
endif

	@rm -rf build cmake cpp mk python java scala golang CMakeLists.txt dut_base.* 2>/dev/null|| true
	@rm -rf ${TARGET}.cpp filelist.f *.fst 2>/dev/null|| true
	@mv ${TARGET}/*.v ${TARGET}/*.sv . 2>/dev/null|| true
endif

coverage:
ifeq ($(COVERAGE), ON)
ifeq ($(SIMULATOR), verilator)
	@rm -rf coverage/
	@verilator_coverage -write-info coverage.info ./V${PROJECT}_coverage.dat
	@genhtml coverage.info --output-directory coverage
else
# TODO: add vcs?
	@echo $(SIMULATOR) TBD
endif
else
	@echo coverage is not on
endif

clean: 