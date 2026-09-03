from . import get_runner


# ==========================================================
# PYTHON
# ==========================================================

python_code = """
n = int(input())
print(n * 2)
"""

runner = get_runner("PYTHON")

result = runner.run(
    code=python_code,
    input_data="10\n"
)

print("\nPYTHON")
print("STATUS:", result.status)
print("OUTPUT:", repr(result.output))
print("ERROR:", result.error)


# ==========================================================
# C
# ==========================================================

c_code = """
#include <stdio.h>

int main()
{
    int n;

    scanf("%d", &n);

    printf("%d\\n", n * 2);

    return 0;
}
"""

runner = get_runner("C")

result = runner.run(
    code=c_code,
    input_data="10\n"
)

print("\nC")
print("STATUS:", result.status)
print("OUTPUT:", repr(result.output))
print("ERROR:", result.error)


# ==========================================================
# C++
# ==========================================================

cpp_code = """
#include <iostream>

using namespace std;

int main()
{
    int n;

    cin >> n;

    cout << n * 2 << endl;

    return 0;
}
"""

runner = get_runner("CPP")

result = runner.run(
    code=cpp_code,
    input_data="10\n"
)

print("\nC++")
print("STATUS:", result.status)
print("OUTPUT:", repr(result.output))
print("ERROR:", result.error)


# ==========================================================
# JAVA
# ==========================================================

java_code = """
import java.util.Scanner;

public class Main {

    public static void main(String[] args) {

        Scanner scanner = new Scanner(System.in);

        int n = scanner.nextInt();

        System.out.println(n * 2);
    }
}
"""

runner = get_runner("JAVA")

result = runner.run(
    code=java_code,
    input_data="10\n"
)

print("\nJAVA")
print("STATUS:", result.status)
print("OUTPUT:", repr(result.output))
print("ERROR:", result.error)