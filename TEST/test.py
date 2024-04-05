import re

input_str = "6   х 456"

# if re.match(r'^\d+([.,]?\d+)?[xXхХ]\d+$', input_str):
# if re.match(r'^\d+([.,]?\d+)?[xX]\d+$', input_str):
if re.match(r'^\d+([.,]?\d+)?\s*[xXхХ]\s*\d+$', input_str):

    weight, repetitions = re.split(r'\s*[xXхХ]\s*', input_str)
    weight = float(weight.replace(',', '.'))
    repetitions = int(repetitions)
    print(weight, repetitions)
    print("Y")
else:
    print("N")