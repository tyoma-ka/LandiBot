import random
import string

def generate_password(length=16):
    # Define characters to use in the password
    characters = string.ascii_letters + string.digits

    # Generate the password by randomly choosing characters
    password = ''.join(random.choice(characters) for i in range(length))

    return password

# Generate a strong password of default length (12 characters)
strong_password = generate_password()
print("Strong Password:", strong_password)
