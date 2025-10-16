# Minimal Makefile for Sphinx
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help html clean

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  html     to build the documentation"
	@echo "  clean    to remove build artifacts"

html:
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" -a -E

clean:
	@rm -rf $(BUILDDIR)/*
	@echo "Cleaned build artifacts"