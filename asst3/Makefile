FILES= code/Makefile \
	code/*.h \
	code/*.cpp 

handin.tar: $(FILES)
	tar cvf handin.tar $(FILES)

clean:
	(cd code; make clean)
	(cd examples; make clean)
	rm -f *~ handin.tar
