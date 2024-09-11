def fizzbuzz(n):
    """
    Generate FizzBuzz sequence up to n.

    Args:
        n (int): The upper limit of the sequence.

    Returns:
        list: A list of strings representing the FizzBuzz sequence.
    """
    result = []
    for i in range(1, n + 1):
        if i % 3 == 0 and i % 5 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result


def main():
    """Run the FizzBuzz script."""
    n = 100
    sequence = fizzbuzz(n)
    for item in sequence:
        print(item)


if __name__ == "__main__":
    main()
