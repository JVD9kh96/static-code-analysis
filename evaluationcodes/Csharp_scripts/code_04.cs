using System;
using System.Collections.Generic;
using System.Linq;

#nullable enable
public static class Perfect04_CliSum
{
    public static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.WriteLine("Usage: Perfect04_CliSum <int> [<int> ...]");
            return 2;
        }

        var ints = new List<int>();
        foreach (var a in args)
        {
            if (!int.TryParse(a, out var v))
            {
                Console.Error.WriteLine($"Invalid integer: {a}");
                return 3;
            }

            // optional range check
            if (v is < -1_000_000_000 or > 1_000_000_000)
            {
                Console.Error.WriteLine($"Integer out of range: {a}");
                return 4;
            }

            ints.Add(v);
        }

        Console.WriteLine(ints.Sum());
        return 0;
    }
}