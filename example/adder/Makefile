WORK_DIR = $(shell pwd)/src
PYTHON 	= python3
PICKER 	= picker
NAME	= Adder

run:
	pytest --mlvp-report -sv .

dut:
	$(PICKER) export --autobuild=true adder.v -w Adder.fst --sname Adder --tdir picker_out_adder --lang python -e -c --sim verilator
	cp -r picker_out_adder/UT_Adder .

clean:
	rm -rf UT_Adder picker_out_adder
