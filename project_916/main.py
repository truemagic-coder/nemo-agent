def fizzbuzz(n):
    """
    Generate FizzBuzz sequence up to n.

    Args:
        n (int): The number up to which the sequence should be generated.

    Returns:
        list: A list containing the FizzBuzz sequence.
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


if __name__ == "__main__":
    print(fizzbuzz(15))
