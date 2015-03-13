#include <stdio.h>
#include <Python.h>
#include "lib.h"

int main() {
	Py_Initialize();
	initlib();
    printf("main: Calling test100000Times() in lib.so...\n");
    test100000Times();
    printf("main: Finished.\n");
    Py_Finalize();
    return 0;
}
