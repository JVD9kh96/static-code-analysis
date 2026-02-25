using System;
using System.Data;
using System.Data.SqlClient;

#nullable enable
public static class Flawed07_SqlInjection
{
    public static object? GetUserByName(IDbConnection conn, string username)
    {
        var sql = "SELECT Id, Username FROM Users WHERE Username = '" + username + "';";
        using var cmd = conn.CreateCommand();
        cmd.CommandText = sql;
        using var rdr = cmd.ExecuteReader();
        return rdr.Read() ? (object?)rdr.GetValue(0) : null;
    }

    public static void Main()
    {
        Console.WriteLine("Example - not connecting anywhere");
    }
}