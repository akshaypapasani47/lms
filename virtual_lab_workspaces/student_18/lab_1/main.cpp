#include <iostream>
#include <string>
using namespace std;

int main() {

    string name;
    int n;

    cout << "Enter your name: ";
    cin >> name;

    cout << "Enter a number: ";
    cin >> n;

    cout << "\nHello, " << name << endl;

    if (n > 0) {
        cout << "Positive number" << endl;
    }
    else if (n < 0) {
        cout << "Negative number" << endl;
    }
    else {
        cout << "Zero" << endl;
    }

    int limit = n < 0 ? -n : n;

    cout << "\nFor loop:" << endl;

    for (int i = 1; i <= limit; i++) {
        cout << i << " ";
    }

    cout << "\n\nWhile loop:" << endl;

    int i = 1;
    int total = 0;

    while (i <= limit) {
        total += i;
        i++;
    }

    cout << "Sum = " << total << endl;

    cout << "\nMultiplication table:" << endl;

    for (i = 1; i <= 10; i++) {
        cout << n << " x " << i
             << " = " << n * i << endl;
    }

    return 0;
}