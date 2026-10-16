# Python Runtime Test
#AKSHAYn2
name = input("Enter your name: ")
n = int(input("Enter a number: "))

print("\nHello,", name)

if n > 0:
    print("Positive number")
elif n < 0:
    print("Negative number")
else:
    print("Zero")

print("\nFor loop:")
for i in range(1, n + 1):
    print(i, end=" ")

print("\n\nWhile loop:")
i = 1
total = 0

while i <= n:
    total += i
    i += 1

print("Sum =", total)

print("\nMultiplication table:")
for i in range(1, 11):
    print(n, "x", i, "=", n * i)