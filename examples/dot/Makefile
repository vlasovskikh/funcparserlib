OUTS = $(wildcard *.dot.out)
DOTS = $(patsubst %.dot.out,%.dot,$(OUTS))
PNGS = $(patsubst %.dot,%.png,$(DOTS))
.PHONY = test png all clean

test:
	../run-tests

all: png test

png: $(PNGS)

%.png: %.dot
	dot -Tpng $< -o $@

clean:
	rm -f $(PNGS)

