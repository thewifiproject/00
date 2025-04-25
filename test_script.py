# Test Python Script
def greet(name):
    return f"Hello, {name}!"

def test_greet():
    assert greet('World') == 'Hello, World!'
    assert greet('Python') == 'Hello, Python!'

if __name__ == "__main__":
    test_greet()
    print("All tests passed successfully!")
