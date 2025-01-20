PYTHON	= python3
PICKER 	= picker
NAME	= Adder


run:
	pytest --toffee-report -sv .

dut:
	$(PICKER) export --autobuild=true adder.v -w Adder.fst --sname Adder --tdir picker_out_adder --lang python -e -c --sim verilator

clean:
	rm -rf UT_Adder picker_out_adder reports
