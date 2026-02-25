using System;

#nullable enable
public static class Flawed11_HighComplexityAndBroadCatch
{
    public static int ComplexCalculation(int x)
    {
        int result = 0;
        if (x % 2 == 0)
        {
            result += 1;
            if (x % 3 == 0)
                result += 2;
            else
            {
                for (int i = 0; i < 3; i++)
                {
                    if (i == 0)
                        result += 3;
                    else if (i == 1)
                        result += 4;
                    else
                        result += 5;
                }
            }
        }
        else
        {
            result -= 1;
        }

        if (x > 10 || (x % 2 != 0 && x < 0))
        {
            result += 6;
            while (x > 0)
            {
                if (x % 5 == 0)
                    result += 7;
                if (x % 7 == 0)
                    result += 8;
                x--;
            }
        }

        try
        {
            if (result < 0)
                throw new ArgumentOutOfRangeException(nameof(result));
            if (result == 0)
                result = 1;
        }
        catch
        {
            // broad catch-all handler
            result = 0;
        }

        for (int j = 0; j < 4; j++)
        {
            if (j % 2 == 0)
                result += j;
            else if (j == 1)
                result -= j;
            else
                result *= j;
        }

        if (result > 100) result /= 2;
        else if (result > 50) result /= 3;
        else if (result > 20) result /= 4;
        else result += 10;

        return result;
    }

    public static void Main()
    {
        Console.WriteLine(ComplexCalculation(42));
    }
}