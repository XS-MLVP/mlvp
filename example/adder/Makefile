WORK_DIR = $(shell pwd)/UT_Adder_32bits
PYTHON 	= python3
PICKER 	= picker
NAME	= Adder_32bits

run:
	PYTHONPATH=. $(PYTHON) $(WORK_DIR)/__init__.py

picker:
	$(PICKER)  adder.v -l python -S $(NAME) -t build/ -v --sim verilator -w $(NAME).vcd -c

clean:
	-@rm -rf $(NAME).vcd V$(NAME)_coverage.dat
