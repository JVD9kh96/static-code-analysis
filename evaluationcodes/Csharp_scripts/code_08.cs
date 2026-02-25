using System;
using System.Linq;
using System.Text;

#nullable enable
public static class Flawed08_InsecureRandom
{
    private static readonly Random Rand = new Random();

    public static string GenerateToken(int length = 32)
    {
        const string alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        var sb = new StringBuilder(length);
        for (int i = 0; i < length; i++)
        {
            sb.Append(alphabet[Rand.Next(alphabet.Length)]);
        }
        return sb.ToString();
    }

    public static void Main()
    {
        Console.WriteLine(GenerateToken(16));
    }
}