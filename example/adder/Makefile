WORK_DIR = $(shell pwd)/src
PYTHON 	= python3
PICKER 	= picker
NAME	= Adder_32bits

run:
	@mkdir report -p
	PYTHONPATH=. $(PYTHON) $(WORK_DIR)/__init__.py

picker:
	$(PICKER)  adder.v -l python -S $(NAME) -t build/  --sim verilator -w $(NAME).vcd -c

clean:
	-@rm -rf report
