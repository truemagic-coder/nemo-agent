import pytest
from main import fizzbuzz

@pytest.mark.parametrize(
    "n, expected",
    [
        (15, ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]),
        (30, ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz", "16", "17", "Fizz", "19", "Buzz", "Fizz", "21", "22", "Fizz", "24", "Buzz", "Fizz", "27", "28", "Fizz", "Buzz", "FizzBuzz"]),
    ]
)
def test_fizzbuzz(n, expected):
    assert fizzbuzz(n) == expected