# Find all numbers between 1 and 10,000 divisible by both 7 and 8

def main():
    numbers = [n for n in range(1, 10001) if n % 7 == 0 and n % 8 == 0]
    print(numbers)


if __name__ == "__main__":
    main()
