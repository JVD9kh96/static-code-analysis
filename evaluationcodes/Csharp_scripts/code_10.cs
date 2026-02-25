using System;

#nullable enable
public static class Flawed10_HardcodedCredential
{
    // hardcoded password in code
    private static readonly string ApiPassword = "SuperSecretPassword123!";

    public static bool Authenticate(string input)
    {
        return input == ApiPassword;
    }

    public static void Main()
    {
        Console.WriteLine("Authenticate by passing a password");
    }
}