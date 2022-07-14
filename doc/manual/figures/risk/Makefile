#
#
#
PNG_TARGETS:=\
exposure-nepal.png \
fragility-continuous.png \
fragility-discrete.png \
io-structure-benefit-cost.png \
io-structure-classical-damage.png \
io-structure-classical-risk.png \
io-structure-event-based-damage.png \
io-structure-event-based-risk.png \
io-structure-scenario-damage.png \
io-structure-scenario-risk.png \
vulnerability-nonzero-cov.png \
vulnerability-zero-cov.png 


all: $(PNG_TARGETS)

.PHONY: clean
clean: 
	/bin/rm -rf $(TARGETS)

$(SVG_TARGETS): %.svg: %.pdf
	inkscape --without-gui --file=$< --export-plain-svg=$@

$(PNG_TARGETS): %.png: %.pdf
	convert -density 300 $< $@

