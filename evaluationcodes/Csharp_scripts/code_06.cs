using System;
using System.Collections.Generic;

#nullable enable
public static class Flawed06_MutableStatic
{
    // shared mutable collection
    public static List<string> Shared = new List<string>();

    public static void AddItem(string item)
    {
        Shared.Add(item);
    }

    public static void Main()
    {
        AddItem("hello");
        Console.WriteLine(string.Join(", ", Shared));
    }
}