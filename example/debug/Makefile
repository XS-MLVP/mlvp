PYTHONPATH := $(shell pwd)/../..:.:./picker_out_mem

export PYTHONPATH

build:
	picker export mem.v --autobuild=true --vpi -w picker_out_mem/mem.vcd --tdir picker_out_mem/mem --lang python

clean:
	rm -rf mem picker_out_*

run:
	python3 example.py
