#include <stdio.h>

int sum(int a, int b) {
    return a + b;
}

long long sum1000000Times(void) {
    long long i;
    long long n;
    n = 0;
    for (i = 1; i <= 1000000; i ++) {
        n = n + i;
    }
    return n;
}

void printSomething(void) {
    printf("Hello world in C module\n");
    return;
}

int main(int argc, char** argv) {
    printSomething();
    return 0;
}
