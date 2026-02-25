using System;
#nullable enable

public record User(int Id, string Username, string Email)
{
    public string GetDisplayName()
    {
        // Keep presentation concerns separate; escape where necessary at rendering boundary.
        return $"{Username} <{Email}>";
    }
}

public static class Perfect02_UserRecordApp
{
    public static int Main()
    {
        var u = new User(1, "alice", "alice@example.com");
        Console.WriteLine(u.GetDisplayName());
        return 0;
    }
}