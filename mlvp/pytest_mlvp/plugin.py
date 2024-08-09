import pytest

@pytest.fixture
def mlvp_test():
    print("This is a test fixture")
    return 1
