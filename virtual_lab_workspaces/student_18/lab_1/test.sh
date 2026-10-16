#!/bin/bash

echo "Enter your name:"
read name

echo "Enter a number:"
read n

echo
echo "Hello, $name"

if [ "$n" -gt 0 ]; then
    echo "Positive number"
elif [ "$n" -lt 0 ]; then
    echo "Negative number"
else
    echo "Zero"
fi

echo
echo "For loop:"

for ((i=1; i<=n; i++))
do
    echo -n "$i "
done

echo
echo
echo "While loop:"

i=1
total=0

while [ "$i" -le "$n" ]
do
    total=$((total + i))
    i=$((i + 1))
done

echo "Sum = $total"

echo
echo "Multiplication table:"

for ((i=1; i<=10; i++))
do
    echo "$n x $i = $((n * i))"
done