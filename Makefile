SE_PREFIX = $(HOME)

CFLAGS = -g -O2 -Wall
CPPFLAGS = -I$(SE_PREFIX)/include
LDFLAGS = -L$(SE_PREFIX)/lib -Wl,-rpath=$(SE_PREFIX)/lib
LDLIBS = -lse

.PHONY: clean

all: burn_query entropy SDF-reader cco2-SDF-reader unburned cco2-unburned update_yields

burn_query:
entropy:
SDF-reader:
cco2-SDF-reader:
unburned:
cco2-unburned:
update_yields:

clean:
	-$(RM) burn_query entropy SDF-reader cco2-SDF-reader unburned cco2-unburned update_yields *.o
