import pytest
import main


@pytest.mark.parametrize("n, expected", [
    (15, [
        "1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
        "11", "Fizz", "13", "14", "FizzBuzz"
    ]),
    (5, ["1", "2", "Fizz", "4", "Buzz"]),
    (3, ["1", "2", "Fizz"]),
    (1, ["1"]),
])
def test_fizzbuzz(n, expected):
    assert main.fizzbuzz(n) == expected


def test_fizzbuzz_empty():
    assert main.fizzbuzz(0) == []