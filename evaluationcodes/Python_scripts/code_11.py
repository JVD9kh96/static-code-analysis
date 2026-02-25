def complex_calculation(x: int) -> int:
    result = 0
    if x % 2 == 0:
        result += 1
        if x % 3 == 0:
            result += 2
        else:
            for i in range(3):
                if i == 0:
                    result += 3
                elif i == 1:
                    result += 4
                else:
                    result += 5
    else:
        result -= 1

    if x > 10 or (x & 1 and x < 0):
        result += 6
        while x > 0:
            if x % 5 == 0:
                result += 7
            if x % 7 == 0:
                result += 8
            x -= 1

    try:
        if result < 0:
            raise ValueError("negative")
        if result == 0:
            result = 1
    except ValueError:
        result = 0
    except Exception:
        result = -1

    for j in range(4):
        if j % 2 == 0:
            result += j
        elif j == 1:
            result -= j
        else:
            result *= j

    if result > 100:
        result //= 2
    elif result > 50:
        result //= 3
    elif result > 20:
        result //= 4
    else:
        result = result + 10

    return result


if __name__ == "__main__":
    print(complex_calculation(42))
