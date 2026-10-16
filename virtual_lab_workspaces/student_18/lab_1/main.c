#include <stdio.h>

int main() {

    char name[50];
    int n;

    printf("Enter your name: ");
    scanf("%49s", name);

    printf("Enter a number: ");
    scanf("%d", &n);

    printf("\nHello, %s\n", name);

    if (n > 0) {
        printf("Positive number\n");
    } else if (n < 0) {
        printf("Negative number\n");
    } else {
        printf("Zero\n");
    }

    printf("\nFor loop:\n");

    int limit = n < 0 ? -n : n;

    for (int i = 1; i <= limit; i++) {
        printf("%d ", i);
    }

    printf("\n\nWhile loop:\n");

    int i = 1;
    int total = 0;

    while (i <= limit) {
        total += i;
        i++;
    }

    printf("Sum = %d\n", total);

    printf("\nMultiplication table:\n");

    for (i = 1; i <= 10; i++) {
        printf("%d x %d = %d\n", n, i, n * i);
    }

    return 0;
}