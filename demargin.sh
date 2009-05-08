#!/bin/sh

# remove margins form PDF files.

pdfcrop gnu-wk-lucida.pdf gnu-wk-lucida-CROP.pdf
pdfcrop --margins "20 20 20 20" gnu-wk-lucida.pdf gnu-wk-lucida-MARGIN-20.pdf


