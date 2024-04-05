num1 = "2.0"
num2 = "120.00"
num3 = "12.50"

num1 = num1.rstrip('0').rstrip(".")  # результат: "2"
num2 = num2.rstrip('0').rstrip(".")  # результат: "120"
num3 = num3.rstrip('0').rstrip(".")  # результат: "12.5"

print(num1, num2, num3)