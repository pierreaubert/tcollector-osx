#!/bin/sh

clang -o t_iostat t_iostat.c -framework CoreFoundation -framework IOKit

grep 'printf("' *.c | awk '{print substr($1,9,40);}' > metrics.txt

