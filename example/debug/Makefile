PYTHONPATH := $(shell pwd)/../..:.:./picker_out_mem

export PYTHONPATH

build_vcs: clean
	picker export mem.v --autobuild=true --vpi -w picker_out_mem/mem.fsdb --tdir picker_out_mem/mem --lang python --sim vcs

build: clean
	picker export mem.v --autobuild=true --vpi -w picker_out_mem/mem.vcd --tdir picker_out_mem/mem --lang python

clean:
	rm -rf *.log mem picker_out_* *.key

run:
	LD_PRELOAD=picker_out_mem/mem/libUTmem.so python3 example.py
