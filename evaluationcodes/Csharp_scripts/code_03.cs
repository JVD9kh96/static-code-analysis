using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

#nullable enable
public static class Perfect03_MatchLines
{
    public static IEnumerable<string> MatchLines(string path, string pattern)
    {
        if (string.IsNullOrWhiteSpace(path)) throw new ArgumentException("path required", nameof(path));
        if (string.IsNullOrWhiteSpace(pattern)) throw new ArgumentException("pattern required", nameof(pattern));

        var file = new FileInfo(path);
        if (!file.Exists) throw new FileNotFoundException("File not found", path);

        Regex regex;
        try
        {
            regex = new Regex(pattern, RegexOptions.Compiled | RegexOptions.CultureInvariant);
        }
        catch (ArgumentException ex)
        {
            throw new ArgumentException("Invalid regex pattern", nameof(pattern), ex);
        }

        using var reader = new StreamReader(file.FullName);
        string? line;
        while ((line = reader.ReadLine()) is not null)
        {
            if (regex.IsMatch(line))
                yield return line;
        }
    }

    // simple runner
    public static int Main(string[] args)
    {
        if (args.Length != 2)
        {
            Console.Error.WriteLine("Usage: Perfect03_MatchLines <file> <regex>");
            return 2;
        }

        foreach (var l in MatchLines(args[0], args[1]))
            Console.WriteLine(l);

        return 0;
    }
}