import java.util.Scanner;

public class Main {
    public static void main(String[] args) {

        Scanner sc = new Scanner(System.in);

        System.out.print("Enter your name: ");
        String name = sc.nextLine();

        System.out.print("Enter a number: ");
        int n = sc.nextInt();

        System.out.println("\nHello, " + name);

        if (n > 0) {
            System.out.println("Positive number");
        } else if (n < 0) {
            System.out.println("Negative number");
        } else {
            System.out.println("Zero");
        }

        System.out.println("\nFor loop:");

        for (int i = 1; i <= Math.abs(n); i++) {
            System.out.print(i + " ");
        }

        System.out.println("\n\nWhile loop:");

        int i = 1;
        int total = 0;

        while (i <= Math.abs(n)) {
            total += i;
            i++;
        }

        System.out.println("Sum = " + total);

        System.out.println("\nMultiplication table:");

        for (i = 1; i <= 10; i++) {
            System.out.println(n + " x " + i + " = " + (n * i));
        }

        sc.close();
    }
}