#
#
#
SVG_TARGETS:=\
arb_mfd.svg \
area.svg \
char_fault1.svg \
char_fault2.svg \
char_fault3.svg \
complex_fault.svg \
dt_mfd.svg \
ed_mfd.svg \
GenericLogicTreeStructure.svg \
gmf-corr.svg \
gmf-no-corr.svg \
hazard-curves-ltcase2.svg \
multi_surface.svg \
point.svg \
point_source_multiple_ruptures.svg \
pointsrc_2strike_2hypodep.svg \
psha_input_structure.svg \
ses.svg \
simple_fault.svg \
single_rupture.svg \
yc_mfd_char_rate.svg \
yc_mfd_moment_rate.svg \
yc_mfd.svg

PNG_TARGETS:=\
arb_mfd.png \
area.png \
char_fault1.png \
char_fault2.png \
char_fault3.png \
complex_fault.png \
dt_mfd.png \
ed_mfd.png \
GenericLogicTreeStructure.png \
gmf-corr.png \
gmf-no-corr.png \
hazard-curves-ltcase2.png \
multi_surface.png \
point.png \
point_source_multiple_ruptures.png \
pointsrc_2strike_2hypodep.png \
psha_input_structure.png \
ses.png \
simple_fault.png \
single_rupture.png \
yc_mfd_char_rate.png \
yc_mfd_moment_rate.png \
yc_mfd.png \

all: $(PNG_TARGETS)

.PHONY: clean
clean: 
	/bin/rm -rf $(TARGETS)

$(SVG_TARGETS): %.svg: %.pdf
	inkscape --without-gui --file=$< --export-plain-svg=$@

$(PNG_TARGETS): %.png: %.pdf
	convert -density 300 $< $@

