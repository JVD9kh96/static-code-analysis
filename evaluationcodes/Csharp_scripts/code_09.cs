using System;
using System.IO;

#nullable enable
public static class Flawed09_PathTraversal
{
    public static string ReadUserFile(string filename)
    {
        var baseDir = Path.Combine(Directory.GetCurrentDirectory(), "uploads");
        var target = Path.Combine(baseDir, filename);
        return File.ReadAllText(target);
    }

    public static void Main()
    {
        Console.WriteLine("Call ReadUserFile with a filename");
    }
}